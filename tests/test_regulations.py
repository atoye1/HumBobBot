import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db # Assuming get_db can be overridden
from models import Regulation
from server import app # Your FastAPI app instance
import datetime
import config # To get REGULATION_CRAWLER_BASE_URL for download links

# Test Database Setup
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///./test_HumBobBot.db"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL_TEST, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# Override get_db dependency for tests
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Test Client
client = TestClient(app)

# Pytest Fixture for Database Setup/Teardown
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine_test) # Create tables
    db = TestingSessionLocal()
    yield db # Provide the session to the test
    db.close()
    Base.metadata.drop_all(bind=engine_test) # Drop tables after test

# Tests for /get_rules endpoint
def test_get_rules_success(db_session):
    # Add sample Regulation data
    regulation1 = Regulation(
        title="테스트 규정 Alpha", type="내규", create_date=datetime.datetime(2023, 1, 1),
        update_date=datetime.datetime(2023, 1, 1), enforce_date=datetime.datetime(2023, 1, 1),
        file_url="/test/alpha.hwp", html_url="test_alpha_2023-01-01/index.html"
    )
    regulation2 = Regulation(
        title="테스트 규정 Beta", type="지침", create_date=datetime.datetime(2023, 2, 1),
        update_date=datetime.datetime(2023, 2, 1), enforce_date=datetime.datetime(2023, 2, 1),
        file_url="/test/beta.pdf", html_url=None # Test case with no HTML
    )
    db_session.add_all([regulation1, regulation2])
    db_session.commit()

    # Make a POST request
    response = client.post("/get_rules", json={"userRequest": {"utterance": "테스트 규정 Alpha"}})
    
    # Assert status code
    assert response.status_code == 200
    
    # Assert response JSON structure
    response_json = response.json()
    assert "template" in response_json
    assert "outputs" in response_json["template"]
    assert len(response_json["template"]["outputs"]) == 1
    assert "carousel" in response_json["template"]["outputs"][0]
    assert "items" in response_json["template"]["outputs"][0]["carousel"]
    assert len(response_json["template"]["outputs"][0]["carousel"]["items"]) > 0

    # Assert that "테스트 규정 Alpha" is found
    card = response_json["template"]["outputs"][0]["carousel"]["items"][0]
    assert card["title"] == "테스트 규정 Alpha"
    
    # Check "바로보기" URL for regulation1
    # TestClient uses http://testhost as the base URL
    expected_web_url = f"http://testhost/regulation/{regulation1.html_url}"
    assert card["buttons"][0]["action"] == "webLink"
    assert card["buttons"][0]["label"] == "바로보기"
    assert card["buttons"][0]["webLinkUrl"] == expected_web_url
    
    # Check "다운로드" URL for regulation1
    expected_download_url = config.REGULATION_CRAWLER_BASE_URL + regulation1.file_url
    assert card["buttons"][1]["action"] == "webLink"
    assert card["buttons"][1]["label"] == "다운로드"
    assert card["buttons"][1]["webLinkUrl"] == expected_download_url

    # Test for regulation2 (no HTML URL)
    response_beta = client.post("/get_rules", json={"userRequest": {"utterance": "테스트 규정 Beta"}})
    assert response_beta.status_code == 200
    response_beta_json = response_beta.json()
    card_beta = response_beta_json["template"]["outputs"][0]["carousel"]["items"][0]
    assert card_beta["title"] == "테스트 규정 Beta"
    # Check that "바로보기" button is missing (or logic for it)
    # Based on current generate_rule_cards, if html_url is None, no "바로보기" button is added.
    # So there should only be one button (다운로드)
    assert len(card_beta["buttons"]) == 1 
    assert card_beta["buttons"][0]["label"] == "다운로드"
    assert card_beta["buttons"][0]["webLinkUrl"] == config.REGULATION_CRAWLER_BASE_URL + regulation2.file_url


def test_get_rules_not_found(db_session):
    # Make a POST request with a query that shouldn't match anything
    response = client.post("/get_rules", json={"userRequest": {"utterance": "없는규정XYZ"}})
    
    # Assert status code
    assert response.status_code == 200
    
    # Assert response indicates that no regulations were found
    response_json = response.json()
    assert "template" in response_json
    assert "outputs" in response_json["template"]
    assert len(response_json["template"]["outputs"]) == 1
    assert "basicCard" in response_json["template"]["outputs"][0]
    assert response_json["template"]["outputs"][0]["basicCard"]["title"] == "관련 규정을 찾지 못했습니다."

# Placeholder for /regulation/update tests (to be implemented in a later step)
# def test_regulation_update_starts_background_task():
#     response = client.post("/regulation/update")
#     assert response.status_code == 202 # Accepted
#     assert response.json() == {"message": "Regulation update process started in the background."}
#     # Further testing of background task execution would require more complex setup (e.g., mocking)
#     # and is beyond the scope of this initial test.
