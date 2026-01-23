# 📐 UX PROPOSAL — Navigation Radar v2.0
## Refonte Menu par Packs/Catégories

**Date :** Janvier 2026  
**Auteur :** Product Design / UX Lead  
**Objectif :** Navigation structurée par packs, professionnelle, adaptée au modèle SaaS

---

## 1. STRUCTURE FINALE DU MENU

### 📌 DESKTOP SIDEBAR

```
┌─────────────────────────────────────┐
│  🎯 RADAR                           │
├─────────────────────────────────────┤
│                                     │
│  ─── RADAR CORE ───────────────     │
│  ☀️  Aujourd'hui                    │
│  📥 Inbox                           │
│  💰 Pipeline                        │
│  📁 Projets                         │
│  🎨 Production                      │
│  📦 Assets                          │
│  📅 Calendrier                      │
│                                     │
│  ─── RADAR BUSINESS ───────────     │  ← Si pack activé
│  💼 Clients                         │
│  📄 Devis                           │
│  🧾 Factures                        │
│                                     │
│  ─── RADAR DISCOVERY ──────────     │  ← Si pack activé
│  🔍 Découverte                      │
│  🎵 Artistes                        │
│  ⚖️  Comparaison                    │
│                                     │
│  ─── RADAR ANALYTICS ──────────     │  ← Si pack activé
│  📊 Cockpit                         │
│  📈 Analytics                       │
│  🗺️  Carte                          │
│  👁️  Veille Concur.                 │
│                                     │
│  ─── RADAR INTELLIGENCE ───────     │  ← Si pack activé
│  ✨ Daily Picks                     │
│  📊 Scoring                         │
│  🎯 Profils                         │
│  🧠 Prédictions IA                  │
│                                     │
│  ─── RADAR DATA ───────────────     │  ← Admin only + Pack
│  📡 Sources                         │
│  💓 Source Health                   │
│                                     │
├─────────────────────────────────────┤
│  ⚙️  Paramètres                     │
│  🏢 Workspace        ← Admin only   │
└─────────────────────────────────────┘
```

### 📱 MOBILE DRAWER

Mêmes sections mais **collapsables** par défaut.  
Seul "Radar Core" est expand par défaut.

```
┌─────────────────────────────────────┐
│  RADAR CORE               ▼ (open)  │
│  ├─ Aujourd'hui                     │
│  ├─ Inbox                           │
│  ├─ Pipeline                        │
│  ├─ Projets                         │
│  ├─ Production                      │
│  ├─ Assets                          │
│  └─ Calendrier                      │
│                                     │
│  RADAR BUSINESS           ▶ (closed)│
│  RADAR DISCOVERY          ▶ (closed)│
│  RADAR ANALYTICS          ▶ (closed)│
│  RADAR INTELLIGENCE       ▶ (closed)│
│  RADAR DATA               ▶ (closed)│
│                                     │
│  ──────────────────────────         │
│  ⚙️ Paramètres                      │
└─────────────────────────────────────┘
```

### 📱 MOBILE BOTTOM NAV (5 tabs)

```
┌─────────────────────────────────────┐
│  Today   Inbox   [+]   Pipeline  ≡  │
│    ☀️     📥     ⊕      💰     ☰   │
└─────────────────────────────────────┘
```

- **Today** → /today
- **Inbox** → /inbox  
- **[+]** → Quick actions (FAB)
- **Pipeline** → /pipeline
- **Menu (≡)** → Ouvre le drawer avec sections collapsables

---

## 2. RÈGLES DE VISIBILITÉ

### Tableau récapitulatif

| Section | Pack requis | Role requis | Affichage |
|---------|-------------|-------------|-----------|
| **Radar Core** | Toujours activé | - | Toujours visible |
| **Radar Business** | `radar_business` addon | - | Si addon activé |
| **Radar Discovery** | `discovery` pack | - | Si pack activé |
| **Radar Analytics** | `analytics` pack | - | Si pack activé |
| **Radar Intelligence** | `intelligence` pack | - | Si pack activé |
| **Radar Data** | `data` pack | Admin | Admin + Pack |
| **Paramètres** | - | - | Toujours visible |
| **Workspace** | - | Admin | Admin uniquement |

### Logique de filtrage

```typescript
// Pseudo-code de visibilité
sections = [
  { id: 'core', visible: true }, // Toujours
  { id: 'business', visible: hasAddon('radar_business') },
  { id: 'discovery', visible: hasPack('discovery') },
  { id: 'analytics', visible: hasPack('analytics') },
  { id: 'intelligence', visible: hasPack('intelligence') },
  { id: 'data', visible: hasPack('data') && isAdmin },
];
```

### Mapping Pack → Section

| Pack Backend | Section Frontend | Conditions |
|--------------|------------------|------------|
| `core` | Radar Core | Toujours |
| `clients` + addon `radar_business` | Radar Business | Addon activé |
| `talents` (discovery, artists, comparison) | Radar Discovery | Pack activé |
| `talents` + `intelligence` (analytics, map, competitive) | Radar Analytics | Pack activé |
| `intelligence` | Radar Intelligence | Pack activé |
| Admin features | Radar Data | isAdmin + pack |

---

## 3. LABELS EXACTS

### Titres des sections (FR)

```typescript
const SECTION_LABELS = {
  core: "Radar Core",
  business: "Radar Business",
  discovery: "Radar Discovery", 
  analytics: "Radar Analytics",
  intelligence: "Radar Intelligence",
  data: "Radar Data",
  settings: "Paramètres"
};
```

### Labels des pages (inchangés)

| Page | Label FR | Icône |
|------|----------|-------|
| /today | Aujourd'hui | Sun |
| /inbox | Inbox | Inbox |
| /pipeline | Pipeline | DollarSign |
| /projects | Projets | FolderOpen |
| /production | Production | Palette |
| /assets | Assets | Package |
| /agency-calendar | Calendrier | Calendar |
| /clients | Clients | Briefcase |
| /devis | Devis | Receipt |
| /factures | Factures | FileCheck |
| /discovery | Découverte | Search |
| /artist-history | Artistes | Music |
| /comparison | Comparaison | GitCompare |
| /cockpit | Cockpit | LayoutDashboard |
| /analytics | Analytics | TrendingUp |
| /map | Carte | Map |
| /competitive | Veille Concur. | Eye |
| /shortlist | Daily Picks | Sparkles |
| /scoring | Scoring | BarChart3 |
| /profiles | Profils | Sliders |
| /predictions | Prédictions IA | Brain |
| /sources | Sources | Rss |
| /source-health | Source Health | HeartPulse |
| /settings | Paramètres | Settings |
| /workspaces | Workspace | Building2 |

---

## 4. PAGE "MODULE NON ACTIVÉ"

### Design

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│          🔒                                         │
│                                                     │
│     Module non activé                               │
│                                                     │
│     "Radar Business n'est pas activé               │
│      pour ce workspace."                           │
│                                                     │
│     ─────────────────────────────                   │
│                                                     │
│     [Si Admin]                                      │
│     ┌─────────────────────────────┐                 │
│     │  Activer dans Paramètres    │                 │
│     └─────────────────────────────┘                 │
│                                                     │
│     [Si Non-Admin]                                  │
│     💡 Contactez un administrateur                 │
│        du workspace pour activer ce module.        │
│                                                     │
│     ┌─────────────────────────────┐                 │
│     │  ← Retour à l'accueil       │                 │
│     └─────────────────────────────┘                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Contenu textuel

**Titre :** Module non activé

**Message :** "[Nom du module] n'est pas activé pour ce workspace."

**CTA Admin :** "Activer dans Paramètres Workspace"  
→ Redirige vers `/workspaces/[id]`

**CTA Non-Admin :** Texte informatif + "Retour à l'accueil"  
→ Redirige vers `/today`

### Pas d'upsell

❌ Pas de pricing  
❌ Pas de "Passez à Premium"  
❌ Pas de CTA commercial

---

## 5. CHECKLIST DE VALIDATION UX

### Scénarios de test

| # | Scénario | Résultat attendu | ✓ |
|---|----------|------------------|---|
| 1 | User MINI sans addons | Voit uniquement Radar Core + Paramètres | ☐ |
| 2 | User STANDARD + Discovery | Voit Core + Discovery + Paramètres | ☐ |
| 3 | User STANDARD + Analytics + Discovery | Voit Core + Discovery + Analytics + Paramètres | ☐ |
| 4 | User PREMIUM (tous packs) | Voit Core + Business + Discovery + Analytics + Intelligence + Paramètres | ☐ |
| 5 | Admin avec pack Data | Voit tout + Radar Data | ☐ |
| 6 | Non-admin avec pack Data actif | Ne voit PAS Radar Data | ☐ |
| 7 | Accès direct URL /devis sans addon Business | Page "Module non activé" | ☐ |
| 8 | Admin accède à /devis sans addon | Page "Module non activé" + CTA activer | ☐ |
| 9 | Assets n'apparaît qu'une fois | Vérifier absence doublon | ☐ |
| 10 | Mobile : sections collapsables | Core expand, autres collapsed | ☐ |
| 11 | Mobile : menu reste scrollable | Pas de hauteur excessive | ☐ |
| 12 | Ordre des sections | Core → Business → Discovery → Analytics → Intelligence → Data → Paramètres | ☐ |

### Critères de succès

- [ ] **5 secondes rule :** Un utilisateur trouve n'importe quelle page en 5 secondes max
- [ ] **Zero confusion :** Pas de "où est X ?" 
- [ ] **Clean menu :** Pas d'éléments grisés/locked visibles
- [ ] **Mobile-first :** Drawer collapsable, bottom nav simple
- [ ] **Pas de doublons :** Assets unique, pas de répétition
- [ ] **Professionnel :** Look "produit agence", pas "outil expérimental"

---

## 6. MIGRATION TECHNIQUE

### Fichiers à modifier

| Fichier | Changement |
|---------|------------|
| `AppLayout.tsx` | Refonte complète navigation par sections |
| `MobileBottomNav.tsx` | Ajout drawer collapsable + sections |
| `subscriptionStore.ts` | Ajout packs discovery, analytics, intelligence, data |
| `/module-not-activated/page.tsx` | Nouvelle page d'accès refusé |

### Nouveau mapping Packs (à ajouter)

```typescript
export type Pack = 
  | 'core' 
  | 'discovery'      // Découverte, Artistes, Comparaison
  | 'analytics'      // Cockpit, Analytics, Carte, Veille
  | 'intelligence'   // Daily Picks, Scoring, Profils, Prédictions
  | 'data';          // Sources, Source Health

export type Addon = 'radar_business'; // Clients, Devis, Factures
```

### Backend : enabled_packs migration

Le backend utilise déjà `enabled_packs: List[str]` sur Workspace.  
Il faudra migrer les valeurs pour correspondre aux nouveaux noms de packs.

---

## 7. PRIORITÉS D'IMPLÉMENTATION

### Phase 1 : Core (Urgent)
1. Refonte AppLayout.tsx avec sections
2. Page module non activé
3. Tests de visibilité

### Phase 2 : Mobile
1. Drawer collapsable
2. Bottom nav mise à jour
3. Tests responsive

### Phase 3 : Polish
1. Animations de transition
2. Persistance état collapsed/expanded
3. Tour onboarding mis à jour

---

## 8. NOTES DESIGN

### Couleurs des sections (optionnel)

| Section | Couleur accent |
|---------|----------------|
| Core | Purple (brand) |
| Business | Blue |
| Discovery | Teal |
| Analytics | Orange |
| Intelligence | Pink |
| Data | Gray |

### Icônes des sections (headers)

| Section | Icône |
|---------|-------|
| Radar Core | `Target` ou `Home` |
| Radar Business | `Briefcase` |
| Radar Discovery | `Compass` |
| Radar Analytics | `BarChart2` |
| Radar Intelligence | `Sparkles` |
| Radar Data | `Database` |

---

**Fin de la proposition UX**

*Document validé le : ____________________*  
*Signature Product : ____________________*  
*Signature Dev : ____________________*
