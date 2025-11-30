set -euo pipefail

BROKER="${BROKER:-kafka:29092}"

echo "Creating Kafka topics on broker: ${BROKER} ..."

docker-compose -f docker/docker-compose.yml exec kafka \
  kafka-topics --create \
    --if-not-exists \
    --topic francetravail_offres_raw \
    --bootstrap-server "${BROKER}" \
    --partitions 3 \
    --replication-factor 1

docker-compose -f docker/docker-compose.yml exec kafka \
  kafka-topics --create \
    --if-not-exists \
    --topic francetravail_offres_dlq \
    --bootstrap-server "${BROKER}" \
    --partitions 1 \
    --replication-factor 1

echo "Current topics:"
docker-compose -f docker/docker-compose.yml exec kafka \
  kafka-topics --list --bootstrap-server "${BROKER}"
