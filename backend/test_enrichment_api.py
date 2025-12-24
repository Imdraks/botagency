"""
Test script for Artist Enrichment API (Viberate Web Scraping)
Run with: python -m backend.test_enrichment_api
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Test the service directly
async def test_enrichment():
    from app.enrichment.config import EnrichmentConfig
    from app.enrichment.service import ArtistEnrichmentService
    
    print("\n" + "="*70)
    print("🎵 ARTIST ENRICHMENT API - TEST (Viberate Web Scraping)")
    print("="*70)
    
    # Configuration
    config = EnrichmentConfig(
        viberate_enabled=True,
        viberate_request_delay=1.5,
        label_resolution_method="latest_release"
    )
    
    spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    
    print(f"\n✅ Config loaded")
    print(f"   Viberate scraping: {'✅ Enabled' if config.viberate_enabled else '❌ Disabled'}")
    print(f"   Spotify ID: {'✅ Set' if spotify_client_id else '❌ Missing'}")
    print(f"   Spotify Secret: {'✅ Set' if spotify_client_secret else '❌ Missing'}")
    
    # Initialize service
    service = ArtistEnrichmentService(
        config=config,
        spotify_client_id=spotify_client_id,
        spotify_client_secret=spotify_client_secret
    )
    
    print("\n" + "-"*70)
    print("TEST 1: Enrich Gims")
    print("-"*70)
    
    try:
        result = await service.enrich(
            "https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv",
            force_refresh=False
        )
        
        print(f"\n✅ Enrichment successful!")
        print(f"\n🎤 Artist: {result.artist.name}")
        print(f"🔗 URL: {result.artist.spotify_url}")
        
        print(f"\n📊 SPOTIFY DATA:")
        print(f"   Genres: {', '.join(result.spotify.genres) if result.spotify.genres else 'N/A'}")
        print(f"   Followers: {result.spotify.followers_total:,}" if result.spotify.followers_total else "   Followers: N/A")
        print(f"   Popularity: {result.spotify.popularity}/100" if result.spotify.popularity else "   Popularity: N/A")
        
        print(f"\n🎧 MONTHLY LISTENERS:")
        if result.monthly_listeners.value:
            print(f"   Value: {result.monthly_listeners.value:,}")
            print(f"   Provider: {result.monthly_listeners.provider}")
            print(f"   Confidence: {result.monthly_listeners.confidence*100:.0f}%")
        else:
            print(f"   ❌ Not available")
        
        print(f"\n📱 SOCIAL STATS:")
        if result.social_stats:
            if result.social_stats.spotify_followers:
                print(f"   Spotify: {result.social_stats.spotify_followers:,}")
            if result.social_stats.youtube_subscribers:
                print(f"   YouTube: {result.social_stats.youtube_subscribers:,}")
            if result.social_stats.instagram_followers:
                print(f"   Instagram: {result.social_stats.instagram_followers:,}")
            if result.social_stats.tiktok_followers:
                print(f"   TikTok: {result.social_stats.tiktok_followers:,}")
        else:
            print(f"   ❌ Not available")
        
        print(f"\n🏢 LABEL:")
        if result.labels.principal:
            print(f"   Principal: {result.labels.principal}")
            print(f"   Method: {result.labels.method}")
            if result.labels.evidence:
                print(f"   Evidence: {len(result.labels.evidence)} releases")
        else:
            print(f"   ❌ Not available")
        
        print(f"\n👔 MANAGEMENT:")
        if result.management.value and result.management.value != "unknown":
            print(f"   Company: {result.management.value}")
            print(f"   Provider: {result.management.provider}")
            if result.management.evidence:
                print(f"   Wikidata Entity: {result.management.evidence.wikidata_entity}")
        else:
            print(f"   ❌ Not available")
        
        if result.notes:
            print(f"\n⚠️  NOTES:")
            for note in result.notes:
                print(f"   - {note}")
        
        # JSON output
        print(f"\n" + "-"*70)
        print("JSON OUTPUT:")
        print("-"*70)
        import json
        print(json.dumps(result.model_dump(), indent=2, default=str))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test metrics
    print("\n" + "-"*70)
    print("TEST 2: Provider Metrics")
    print("-"*70)
    
    metrics = service.get_metrics()
    
    for provider_name, stats in metrics.items():
        print(f"\n{provider_name}:")
        print(f"   Requests: {stats['requests']}")
        print(f"   Success Rate: {stats['success_rate']*100:.1f}%")
        print(f"   Failure Rate: {stats['failure_rate']*100:.1f}%")
        print(f"   Cache Hit Rate: {stats['cache_hit_rate']*100:.1f}%")
        print(f"   Avg Latency: {stats['avg_latency']:.2f}s")
        print(f"   Circuit Breaker: {stats['circuit_breaker_state']}")
    
    print("\n" + "="*70)
    print("✅ Tests completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_enrichment())
