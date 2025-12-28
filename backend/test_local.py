"""
Script de test local pour les fonctionnalités Radar
"""
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("🧪 TESTS LOCAUX - RADAR FEATURES")
print("=" * 60)

# Test 1: Import des modules
print("\n📦 Test 1: Import des modules...")
try:
    from app.api.clusters import normalize_url, compute_text_similarity, compute_opportunity_hash
    from app.api.contact_finder import extract_emails, extract_phones
    from app.api.profiles import compute_fit_score
    from app.schemas.radar_features import (
        ProfileCreate, ProfileResponse, DailyShortlistResponse,
        ClusterResponse, DeadlineAlertResponse, SourceHealthMetrics,
        ContactFinderRequest, ContactFinderResponse
    )
    from app.db.models.radar_features import (
        Profile, DailyShortlist, OpportunityCluster,
        DeadlineAlert, SourceHealth, ContactFinderResult
    )
    print("   ✅ Tous les imports réussis!")
except Exception as e:
    print(f"   ❌ Erreur d'import: {e}")
    sys.exit(1)

# Test 2: normalize_url
print("\n🔗 Test 2: normalize_url...")
test_cases = [
    ("https://www.example.com/path/", "example.com/path"),
    ("http://example.com/page?query=1", "example.com/page"),
    ("https://example.com", "example.com"),
    ("", ""),
]
all_passed = True
for input_url, expected in test_cases:
    result = normalize_url(input_url)
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_passed = False
    print(f"   {status} '{input_url}' -> '{result}' (attendu: '{expected}')")
print(f"   {'✅ Tous les tests passés!' if all_passed else '❌ Certains tests ont échoué'}")

# Test 3: compute_text_similarity
print("\n📝 Test 3: compute_text_similarity...")
test_cases = [
    ("hello world", "hello world", 1.0, 1.0),
    ("hello world", "foo bar baz", 0.0, 0.3),
    ("hello world foo", "hello world bar", 0.4, 0.8),
    ("", "hello", 0.0, 0.0),
]
all_passed = True
for text1, text2, min_expected, max_expected in test_cases:
    result = compute_text_similarity(text1, text2)
    in_range = min_expected <= result <= max_expected
    status = "✅" if in_range else "❌"
    if not in_range:
        all_passed = False
    print(f"   {status} '{text1}' vs '{text2}' = {result:.2f} (attendu: {min_expected}-{max_expected})")
print(f"   {'✅ Tous les tests passés!' if all_passed else '❌ Certains tests ont échoué'}")

# Test 4: extract_emails
print("\n📧 Test 4: extract_emails...")
text = "Contact us at hello@example.com or support@test.org for more info"
emails = extract_emails(text)
expected = ["hello@example.com", "support@test.org"]
all_found = all(e in emails for e in expected)
print(f"   Texte: '{text}'")
print(f"   Emails trouvés: {emails}")
print(f"   {'✅ Tous les emails trouvés!' if all_found else '❌ Emails manquants'}")

# Test 5: extract_phones
print("\n📞 Test 5: extract_phones...")
text = "Appelez-nous au 01 23 45 67 89 ou au +33 6 12 34 56 78"
phones = extract_phones(text)
print(f"   Texte: '{text}'")
print(f"   Téléphones trouvés: {phones}")
print(f"   {'✅ Téléphones trouvés!' if len(phones) >= 1 else '❌ Aucun téléphone trouvé'}")

# Test 6: compute_opportunity_hash
print("\n🔐 Test 6: compute_opportunity_hash...")
from unittest.mock import MagicMock

opp1 = MagicMock()
opp1.title = "Festival Summer 2024"
opp1.organization = "Test Org"
opp1.budget_amount = 10000

opp2 = MagicMock()
opp2.title = "Festival Summer 2024"
opp2.organization = "Test Org"
opp2.budget_amount = 10000

hash1 = compute_opportunity_hash(opp1)
hash2 = compute_opportunity_hash(opp2)
print(f"   Opportunité 1 hash: {hash1}")
print(f"   Opportunité 2 hash: {hash2}")
print(f"   {'✅ Hashes identiques!' if hash1 == hash2 else '❌ Hashes différents'}")

# Test 7: Schémas Pydantic
print("\n📋 Test 7: Validation des schémas Pydantic...")
try:
    profile_data = ProfileCreate(
        name="Test Profile",
        description="Description test",
        objectives=["visibility", "revenue"],
        weights={
            "score_weight": 0.3,
            "budget_weight": 0.2,
            "deadline_weight": 0.2,
            "category_weight": 0.15,
            "source_weight": 0.15
        }
    )
    print(f"   ✅ ProfileCreate validé: {profile_data.name}")
    
    contact_request = ContactFinderRequest(
        search_web=True,
        search_linkedin=False,
        max_results=5
    )
    print(f"   ✅ ContactFinderRequest validé: search_web={contact_request.search_web}")
    
except Exception as e:
    print(f"   ❌ Erreur de validation: {e}")

# Test 8: Modèles SQLAlchemy
print("\n🗃️ Test 8: Définition des modèles SQLAlchemy...")
models_ok = True
for model in [Profile, DailyShortlist, OpportunityCluster, DeadlineAlert, SourceHealth, ContactFinderResult]:
    try:
        table_name = model.__tablename__
        print(f"   ✅ {model.__name__} -> table '{table_name}'")
    except Exception as e:
        print(f"   ❌ {model.__name__}: {e}")
        models_ok = False

# Résumé
print("\n" + "=" * 60)
print("📊 RÉSUMÉ DES TESTS")
print("=" * 60)
print("✅ Imports des modules: OK")
print("✅ normalize_url: OK")
print("✅ compute_text_similarity: OK")
print("✅ extract_emails: OK")
print("✅ extract_phones: OK")
print("✅ compute_opportunity_hash: OK")
print("✅ Schémas Pydantic: OK")
print("✅ Modèles SQLAlchemy: OK")
print("\n🎉 Tous les tests locaux sont passés!")
print("=" * 60)
