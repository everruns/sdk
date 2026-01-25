# Image Attachments

Demonstrates attaching images to messages.

## Covered Scenarios

- **Base64 image**: Embed image data directly in message
- **Image URL**: Reference external image URL
- **Uploaded image**: Upload via images API and reference by ID

## Run

```bash
export EVERRUNS_ORG=your-org
export EVERRUNS_API_KEY=your-key
# Optional: export EVERRUNS_API_URL=http://localhost:8080/api

cargo run -p image-attachments
```

## Key Patterns

```rust
// Using base64 encoded image
let content = vec![
    ContentPart::Image {
        base64: Some(base64_data),
        url: None,
    },
    ContentPart::Text {
        text: "What's in this image?".to_string(),
    },
];

// Using image URL
let content = vec![
    ContentPart::Image {
        url: Some("https://example.com/image.png".to_string()),
        base64: None,
    },
    ContentPart::Text {
        text: "Describe this image.".to_string(),
    },
];

// Using uploaded image ID
let content = vec![
    ContentPart::ImageFile {
        image_id: "img_abc123".to_string(),
    },
    ContentPart::Text {
        text: "What do you see?".to_string(),
    },
];
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/images` | Upload image |
| GET | `/images/{id}` | Get image metadata |
