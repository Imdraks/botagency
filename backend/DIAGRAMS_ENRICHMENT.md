# Diagrammes Architecture - Artist Enrichment API

## Diagramme 1: Flow d'Enrichissement Simple

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Service
    participant Apify
    participant Spotify
    participant Wikidata

    User->>API: POST /enrichment/artists/enrich
    API->>Service: enrich(artist_id)
    
    par Appels Parallèles
        Service->>Apify: Fetch monthly listeners
        Apify-->>Service: 18,500,000
        
        Service->>Spotify: Fetch artist data
        Spotify-->>Service: genres, followers, popularity
        
        Service->>Spotify: Fetch albums
        Spotify-->>Service: Album list with labels
        
        Service->>Wikidata: SPARQL query
        Wikidata-->>Service: Management info
    end
    
    Service->>Service: Resolve principal label
    Service->>Service: Aggregate results
    Service-->>API: EnrichedArtistData
    API-->>User: JSON response
```

## Diagramme 2: Retry & Circuit Breaker

```mermaid
sequenceDiagram
    participant Service
    participant Provider
    participant CircuitBreaker
    participant ExternalAPI

    Service->>Provider: get(artist_id)
    Provider->>CircuitBreaker: Check state
    
    alt Circuit CLOSED
        CircuitBreaker-->>Provider: OK, proceed
        Provider->>ExternalAPI: Request
        
        alt Success
            ExternalAPI-->>Provider: Data
            Provider-->>Service: Return data
        else Failure
            ExternalAPI-->>Provider: Error
            Provider->>Provider: Retry (wait 2s)
            Provider->>ExternalAPI: Request (attempt 2)
            
            alt Still Failing
                ExternalAPI-->>Provider: Error
                Provider->>Provider: Retry (wait 4s)
                Provider->>ExternalAPI: Request (attempt 3)
                
                alt Final Failure
                    ExternalAPI-->>Provider: Error
                    Provider->>CircuitBreaker: Record failure
                    CircuitBreaker->>CircuitBreaker: failures >= 5 → OPEN
                    Provider-->>Service: null
                end
            end
        end
    else Circuit OPEN
        CircuitBreaker-->>Provider: Reject immediately
        Provider-->>Service: null (circuit open)
    end
```

## Diagramme 3: Cache Flow

```mermaid
flowchart TD
    A[User Request] --> B{Cache Check}
    B -->|Hit 65%| C[Return Cached Data]
    B -->|Miss 35%| D[Fetch from Provider]
    D --> E{Provider Success?}
    E -->|Yes| F[Store in Cache]
    E -->|No| G[Return null]
    F --> H[Return Fresh Data]
    C --> I[Response to User]
    H --> I
    G --> I
    
    style B fill:#90EE90
    style C fill:#87CEEB
    style F fill:#FFB6C1
```

## Diagramme 4: Architecture Complète

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Next.js UI]
    end
    
    subgraph "API Layer"
        API[FastAPI Endpoints]
        Auth[JWT Authentication]
        Valid[Pydantic Validation]
    end
    
    subgraph "Service Layer"
        Service[ArtistEnrichmentService]
        Orch[Orchestration Logic]
    end
    
    subgraph "Provider Layer"
        Base[BaseProvider]
        ML[MonthlyListenersProvider]
        SP[SpotifyProvider]
        LR[LabelResolver]
        WD[WikidataProvider]
    end
    
    subgraph "Infrastructure"
        Retry[Retry Logic]
        CB[Circuit Breaker]
        Cache[Cache TTL]
        Metrics[Metrics Collector]
    end
    
    subgraph "External APIs"
        Apify[Apify Actor]
        SpotifyAPI[Spotify Web API]
        WikidataAPI[Wikidata SPARQL]
    end
    
    UI --> API
    API --> Auth
    Auth --> Valid
    Valid --> Service
    Service --> Orch
    Orch --> ML
    Orch --> SP
    Orch --> LR
    Orch --> WD
    
    ML --> Base
    SP --> Base
    WD --> Base
    
    Base --> Retry
    Base --> CB
    Base --> Cache
    Base --> Metrics
    
    ML --> Apify
    SP --> SpotifyAPI
    WD --> WikidataAPI
    
    style Service fill:#FFD700
    style Base fill:#98FB98
    style ML fill:#87CEEB
    style SP fill:#87CEEB
    style LR fill:#87CEEB
    style WD fill:#87CEEB
```

## Diagramme 5: Batch Processing

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Service
    participant Apify
    participant Other

    User->>API: POST /batch/enrich [50 artists]
    API->>Service: enrich_batch([id1, ..., id50])
    
    Service->>Apify: Single batch call (50 URLs)
    Note over Apify: 1 Apify run for all
    Apify-->>Service: 50 results
    
    par Individual Provider Calls
        loop For each artist
            Service->>Other: Get Spotify data
            Service->>Other: Get Wikidata info
            Service->>Service: Resolve label
        end
    end
    
    Service->>Service: Aggregate all results
    Service-->>API: List[EnrichedArtistData]
    API-->>User: JSON array [50 items]
```

## Diagramme 6: Circuit Breaker States

```mermaid
stateDiagram-v2
    [*] --> CLOSED
    CLOSED --> OPEN: 5+ failures
    OPEN --> HALF_OPEN: 60s timeout
    HALF_OPEN --> CLOSED: Success
    HALF_OPEN --> OPEN: Failure
    
    note right of CLOSED
        Normal operation
        All requests pass
    end note
    
    note right of OPEN
        Fast fail mode
        All requests rejected
    end note
    
    note right of HALF_OPEN
        Testing mode
        1 request allowed
    end note
```

## Diagramme 7: Label Resolution Logic

```mermaid
flowchart TD
    Start[Start Label Resolution] --> Apify{Apify has labels?}
    Apify -->|Yes| UseApify[Use Apify releases]
    Apify -->|No| Spotify{Spotify albums?}
    Spotify -->|Yes| UseSpotify[Use Spotify albums]
    Spotify -->|No| NoLabel[No label available]
    
    UseApify --> Dedup[Deduplicate releases]
    UseSpotify --> Dedup
    
    Dedup --> Method{Resolution method?}
    Method -->|latest_release| Latest[Sort by date desc]
    Method -->|most_frequent| Frequent[Count frequency]
    
    Latest --> LatestLabel[principal = releases[0].label]
    Frequent --> FreqLabel[principal = most_common label]
    
    LatestLabel --> Evidence[Build evidence trail]
    FreqLabel --> Evidence
    NoLabel --> Null[principal = null]
    
    Evidence --> Return[Return LabelsData]
    Null --> Return
    
    Return --> End[End]
    
    style Start fill:#90EE90
    style Return fill:#FFB6C1
    style End fill:#90EE90
```

## Diagramme 8: Métriques & Monitoring

```mermaid
graph LR
    subgraph "Providers"
        ML[Monthly Listeners]
        SP[Spotify]
        WD[Wikidata]
    end
    
    subgraph "Metrics Collected"
        Req[Requests Count]
        Succ[Success Rate]
        Fail[Failure Rate]
        Cache[Cache Hit Rate]
        Lat[Avg Latency]
        CB[Circuit Breaker State]
    end
    
    subgraph "Monitoring"
        API[Metrics Endpoint]
        Dash[Dashboard]
        Alert[Alerts]
    end
    
    ML --> Req
    ML --> Succ
    ML --> Fail
    ML --> Cache
    ML --> Lat
    ML --> CB
    
    SP --> Req
    SP --> Succ
    SP --> Cache
    SP --> Lat
    SP --> CB
    
    WD --> Req
    WD --> Succ
    WD --> Cache
    WD --> Lat
    WD --> CB
    
    Req --> API
    Succ --> API
    Fail --> API
    Cache --> API
    Lat --> API
    CB --> API
    
    API --> Dash
    API --> Alert
    
    style ML fill:#87CEEB
    style SP fill:#87CEEB
    style WD fill:#87CEEB
    style API fill:#FFD700
```

## Diagramme 9: Data Flow Production

```mermaid
flowchart TD
    subgraph "User Actions"
        Search[Artist Search]
        View[View Details]
        Batch[Daily Refresh]
    end
    
    subgraph "API Layer"
        Enrich[POST /enrich]
        Get[GET /artists/:id]
        BatchAPI[POST /batch/enrich]
    end
    
    subgraph "Service Layer"
        Service[ArtistEnrichmentService]
        Cache{Cache?}
    end
    
    subgraph "Data Sources"
        Apify[Apify Monthly Listeners]
        Spotify[Spotify Web API]
        Wiki[Wikidata SPARQL]
    end
    
    subgraph "Storage"
        Redis[(Redis Cache)]
        DB[(PostgreSQL)]
    end
    
    Search --> Enrich
    View --> Get
    Batch --> BatchAPI
    
    Enrich --> Service
    Get --> Service
    BatchAPI --> Service
    
    Service --> Cache
    Cache -->|Hit| Redis
    Cache -->|Miss| Apify
    Cache -->|Miss| Spotify
    Cache -->|Miss| Wiki
    
    Apify --> Redis
    Spotify --> Redis
    Wiki --> Redis
    
    Service --> DB
    
    style Service fill:#FFD700
    style Cache fill:#90EE90
    style Redis fill:#FFB6C1
    style DB fill:#87CEEB
```

## Diagramme 10: Error Handling

```mermaid
flowchart TD
    Start[Provider.get] --> Try{Try fetch}
    
    Try -->|Success| Cache[Cache result]
    Cache --> Return[Return data]
    
    Try -->|Error| Retry1{Retry 1}
    Retry1 -->|Wait 2s| Try2{Try again}
    
    Try2 -->|Success| Cache
    Try2 -->|Error| Retry2{Retry 2}
    
    Retry2 -->|Wait 4s| Try3{Try again}
    
    Try3 -->|Success| Cache
    Try3 -->|Error| CB{Circuit Breaker}
    
    CB -->|failures < 5| RecordFail[Record failure]
    CB -->|failures >= 5| OpenCB[Open Circuit]
    
    RecordFail --> ReturnNull[Return null]
    OpenCB --> ReturnNull
    
    Return --> End[End]
    ReturnNull --> End
    
    style Start fill:#90EE90
    style Return fill:#98FB98
    style ReturnNull fill:#FF6B6B
    style OpenCB fill:#FFA500
    style End fill:#90EE90
```
