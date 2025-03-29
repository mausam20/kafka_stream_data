# Kafka to BigQuery Ingestion

This application consumes messages from a Kafka topic and ingests the data into a Google BigQuery table. It processes the data, performs transformations, and handles errors during insertion.

## Prerequisites

Ensure you have the following installed:
- Python 3.x
- Google Cloud SDK
- Kafka
- Required Python libraries:
  ```bash
  pip install kafka-python google-cloud-bigquery
  ```
- A valid Google Cloud service account with BigQuery permissions.
- A Kafka topic containing structured JSON messages.

## Configuration

Create a `config.json` file with the following structure:
```json
{
  "environment": "development",
  "development": {
    "kafka": {
      "TOPIC": "your_kafka_topic",
      "BOOT_STRAP": "kafka_broker_address"
    },
    "google_cred_path": "path/to/google_credentials.json",
    "bquery_dataset_id": "your_dataset",
    "bquery_table_id": "your_table",
    "bad_comment_regex": "bad_word_pattern",
    "table_columns": ["column1", "column2", "column3"]
  }
}
```

## Running the Application

1. Set the environment variable for Google credentials:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=path/to/google_credentials.json
   ```
2. Run the script:
   ```bash
   python kafka_bq_ingestion.py
   ```

## Functionality

1. **Kafka Consumer Initialization**
   - Connects to Kafka brokers.
   - Listens to messages from the configured topic.
   - Uses manual offset commits.

2. **Data Processing & Transformation**
   - Parses JSON messages.
   - Performs transformations (e.g., timestamp formatting, field mappings).
   - Flags inappropriate comments using a regex pattern.

3. **BigQuery Ingestion**
   - Inserts transformed records into the specified BigQuery table.
   - Logs errors and retries failed inserts.
   - Commits Kafka offsets upon successful insertion.

## Error Handling

- Logs issues in `app.log`.
- Failed insertions are stored in `errors_insert_records.json`.
- Handles connection failures, transformation errors, and insertion failures.

## Logs & Monitoring

- Uses `logging` to track application status.
- Prints structured logs for debugging.
- Kafka consumer errors are logged in `app.log`.

## Graceful Shutdown

- Handles `KeyboardInterrupt` (Ctrl+C) to close the Kafka consumer properly.

## Future Enhancements

- Implement batch processing for better efficiency.
- Use a message queue for failed records.
- Add automated monitoring and alerts.



