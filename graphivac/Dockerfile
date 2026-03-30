FROM eclipse-temurin:21-jre-alpine

# Install curl for the health check
RUN apk add --no-cache curl

WORKDIR /app

# Download the Graphivac server JAR at image-build time.
# Bump GRAPHIVAC_VERSION + rebuild to upgrade (data in /data volume is unaffected).
ARG GRAPHIVAC_VERSION=1.1.6
RUN curl -fSL "https://hvac.io/graphivac/graphivac-${GRAPHIVAC_VERSION}-standalone.jar" \
    -o graphivac-server.jar

# Data directory — licence, org config, and grid data are written here at runtime.
# Mount a named volume at /data so data survives container restarts and image upgrades.
RUN mkdir -p /data

EXPOSE 3000

# Health check: the default "public" org is created automatically on first start.
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/api/v1/orgs/public || exit 1

# Graphivac writes its working files relative to the current directory.
# Set WORKDIR to /data so all persistent state lands in the mounted volume.
WORKDIR /data

CMD ["java", "-jar", "/app/graphivac-server.jar", "-p", "3000"]

