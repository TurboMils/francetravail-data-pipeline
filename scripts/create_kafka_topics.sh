set -euo pipefail

DOCKER_COMPOSE="docker-compose -f docker/docker-compose.yml"

RAW_TOPIC="francetravail.offres.raw"
DLQ_TOPIC="francetravail.offres.dlq"

echo "Creating Kafka topics ..."

$DOCKER_COMPOSE exec kafka bash -c "
  kafka-topics --create \
    --topic ${RAW_TOPIC} \
    --bootstrap-server kafka:9092 \
    --replication-factor 1 \
    --partitions 3 \
    --if-not-exists
"

$DOCKER_COMPOSE exec kafka bash -c "
  kafka-topics --create \
    --topic ${DLQ_TOPIC} \
    --bootstrap-server kafka:9092 \
    --replication-factor 1 \
    --partitions 1 \
    --if-not-exists
"

echo "Topics created:"
$DOCKER_COMPOSE exec kafka bash -c "kafka-topics --list --bootstrap-server kafka:9092"
