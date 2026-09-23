from backend.main import get_or_create_profile, save_profile_to_disk, persist_resume_analysis_score


def test_resume_analysis_persists_score():
    email = "demo_user@example.com"
    profile = get_or_create_profile(email)
    profile["resume_uploaded"] = True
    profile["resume_score"] = "-"
    save_profile_to_disk(profile)

    persist_resume_analysis_score(email, 82)

    saved = get_or_create_profile(email)
    assert saved["resume_score"] == 82
