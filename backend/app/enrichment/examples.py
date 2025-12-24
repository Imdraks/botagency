"""
Example usage of the Artist Enrichment API (Viberate Web Scraping)
"""
import asyncio
import os
from app.enrichment.config import EnrichmentConfig
from app.enrichment.service import ArtistEnrichmentService


async def example_single_artist():
    """Example: Enrich a single artist (Gims)"""
    
    # Configuration
    config = EnrichmentConfig(
        viberate_enabled=True,
        viberate_request_delay=1.5,
        label_resolution_method="latest_release"
    )
    
    # Initialize service
    service = ArtistEnrichmentService(
        config=config,
        spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", "")
    )
    
    # Enrich artist
    print("🎵 Enriching Gims...")
    result = await service.enrich(
        "https://open.spotify.com/artist/2pvfGvbL4mouaDY9ZSwUmv",
        force_refresh=False
    )
    
    # Display results
    print("\n" + "="*60)
    print(f"🎤 Artist: {result.artist.name}")
    print(f"🎧 Monthly Listeners: {result.monthly_listeners.value:,}")
    print(f"👥 Spotify Followers: {result.social_stats.spotify_followers:,}" if result.social_stats.spotify_followers else "")
    print(f"📺 YouTube: {result.social_stats.youtube_subscribers:,}" if result.social_stats.youtube_subscribers else "")
    print(f"📸 Instagram: {result.social_stats.instagram_followers:,}" if result.social_stats.instagram_followers else "")
    print(f"🎵 TikTok: {result.social_stats.tiktok_followers:,}" if result.social_stats.tiktok_followers else "")
    print(f"⭐ Popularity: {result.spotify.popularity}/100")
    print(f"🎵 Genres: {', '.join(result.spotify.genres)}")
    print(f"🏢 Label: {result.labels.principal}")
    print(f"👔 Management: {result.management.value}")
    print("="*60)
    
    if result.notes:
        print("\n⚠️  Notes:")
        for note in result.notes:
            print(f"  - {note}")
    
    # Close service
    await service.close()
    
    return result


async def example_batch_artists():
    """Example: Enrich multiple artists in batch"""
    
    config = EnrichmentConfig(
        viberate_enabled=True,
        viberate_request_delay=1.5
    )
    
    service = ArtistEnrichmentService(
        config=config,
        spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", "")
    )
    
    # Batch of French artists
    artists = [
        "2pvfGvbL4mouaDY9ZSwUmv",  # Gims
        "7bXgB6jMjp9ATFy66eO08Z",  # Niska
        "1Xyo4u8uXC1ZmMpatF05PJ",  # The Weeknd
    ]
    
    print(f"🎵 Enriching {len(artists)} artists in batch...")
    results = await service.enrich_batch(artists)
    
    print("\n" + "="*60)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.artist.name}")
        print(f"   Listeners: {result.monthly_listeners.value:,}" if result.monthly_listeners.value else "   Listeners: N/A")
        print(f"   Label: {result.labels.principal}")
        print()
    print("="*60)
    
    await service.close()
    
    return results


async def example_with_metrics():
    """Example: Get provider metrics"""
    
    config = EnrichmentConfig(
        viberate_enabled=True
    )
    
    service = ArtistEnrichmentService(
        config=config,
        spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", "")
    )
    
    # Make some requests
    await service.enrich("2pvfGvbL4mouaDY9ZSwUmv")
    await service.enrich("7bXgB6jMjp9ATFy66eO08Z")
    
    # Get metrics
    metrics = service.get_metrics()
    
    print("\n" + "="*60)
    print("📊 Provider Metrics")
    print("="*60)
    
    for provider_name, stats in metrics.items():
        print(f"\n{provider_name}:")
        print(f"  Requests: {stats['requests']}")
        print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
        print(f"  Cache Hit Rate: {stats['cache_hit_rate']*100:.1f}%")
        print(f"  Avg Latency: {stats['avg_latency']:.2f}s")
        print(f"  Circuit Breaker: {stats['circuit_breaker_state']}")
    
    await service.close()
    print("="*60)


async def example_label_resolution_comparison():
    """Example: Compare label resolution methods"""
    
    # Method 1: Latest Release
    config_latest = EnrichmentConfig(
        viberate_enabled=True,
        label_resolution_method="latest_release"
    )
    
    service_latest = ArtistEnrichmentService(
        config=config_latest,
        spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", "")
    )
    
    result_latest = await service_latest.enrich("2pvfGvbL4mouaDY9ZSwUmv")
    
    # Method 2: Most Frequent
    config_frequent = EnrichmentConfig(
        viberate_enabled=True,
        label_resolution_method="most_frequent",
        label_most_frequent_count=20
    )
    
    service_frequent = ArtistEnrichmentService(
        config=config_frequent,
        spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", "")
    )
    
    result_frequent = await service_frequent.enrich("2pvfGvbL4mouaDY9ZSwUmv")
    
    print("\n" + "="*60)
    print("🏷️  Label Resolution Comparison")
    print("="*60)
    print(f"\nLatest Release Method: {result_latest.labels.principal}")
    print(f"Most Frequent Method: {result_frequent.labels.principal}")
    
    if result_latest.labels.evidence:
        print(f"\nEvidence (Latest Release):")
        for ev in result_latest.labels.evidence[:3]:
            print(f"  - {ev.release_name} ({ev.release_date}): {ev.label}")
    
    await service_latest.close()
    await service_frequent.close()
    print("="*60)


async def example_error_handling():
    """Example: Demonstrate error handling and fallbacks"""
    
    config = EnrichmentConfig(
        viberate_enabled=False,  # Disabled for testing
        max_retries=2
    )
    
    service = ArtistEnrichmentService(
        config=config,
        spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", "")
    )
    
    print("🧪 Testing error handling (Viberate disabled)...")
    result = await service.enrich("2pvfGvbL4mouaDY9ZSwUmv")
    
    print("\n" + "="*60)
    print("🎤 Result with partial failure:")
    print(f"  Spotify Data: {'✅' if result.spotify.genres else '❌'}")
    print(f"  Monthly Listeners: {'✅' if result.monthly_listeners.value else '❌'}")
    print(f"  Labels: {'✅' if result.labels.principal else '❌'}")
    print(f"  Management: {'✅' if result.management.value else '❌'}")
    
    if result.notes:
        print("\n⚠️  Notes:")
        for note in result.notes:
            print(f"  - {note}")
    
    await service.close()
    print("="*60)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║   Artist Enrichment API - Examples (Viberate Scraping)    ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Run examples
    print("\n1️⃣  Single Artist Enrichment")
    asyncio.run(example_single_artist())
    
    print("\n\n2️⃣  Batch Enrichment")
    asyncio.run(example_batch_artists())
    
    print("\n\n3️⃣  Provider Metrics")
    asyncio.run(example_with_metrics())
    
    print("\n\n4️⃣  Label Resolution Comparison")
    asyncio.run(example_label_resolution_comparison())
    
    print("\n\n5️⃣  Error Handling")
    asyncio.run(example_error_handling())
    
    print("\n✅ All examples completed!")
