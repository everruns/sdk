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

#[test]
fn test_base_url_normalization_adds_trailing_slash() {
    // Base URL without trailing slash should be normalized to have one
    let client = Everruns::with_base_url("evr_test_key", "https://custom.example.com/api")
        .expect("client creation should succeed");

    // Debug output includes the base_url field
    let debug_str = format!("{:?}", client);
    // The base URL should have a trailing slash after normalization
    assert!(
        debug_str.contains("https://custom.example.com/api/"),
        "base URL should be normalized with trailing slash"
    );
}

#[test]
fn test_base_url_normalization_preserves_trailing_slash() {
    // Base URL with trailing slash should remain unchanged
    let client = Everruns::with_base_url("evr_test_key", "https://custom.example.com/api/")
        .expect("client creation should succeed");

    let debug_str = format!("{:?}", client);
    assert!(
        debug_str.contains("https://custom.example.com/api/"),
        "base URL with trailing slash should be preserved"
    );
}
