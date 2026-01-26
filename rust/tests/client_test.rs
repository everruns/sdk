//! Integration tests for Everruns SDK

use everruns_sdk::Everruns;

#[test]
fn test_client_creation() {
    let result = Everruns::new("evr_test_key");
    assert!(result.is_ok());
}

#[test]
fn test_client_from_env_missing() {
    // Ensure env var is not set
    // SAFETY: This test runs single-threaded and only removes a test-specific env var
    unsafe { std::env::remove_var("EVERRUNS_API_KEY") };
    let result = Everruns::from_env();
    assert!(result.is_err());
}

#[test]
fn test_custom_base_url() {
    let result = Everruns::with_base_url("evr_test_key", "https://custom.example.com/api");
    assert!(result.is_ok());
}
