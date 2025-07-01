# Análisis de Tráfico - Sistema Distribuido

Sistema distribuido para análisis de datos de tráfico de Waze utilizando Docker, MongoDB, Redis, Apache Pig y Elasticsearch.

## Arquitectura

- **MongoDB**: Base de datos principal
- **Redis**: Sistema de caché
- **Apache Pig**: Procesamiento de datos
- **Elasticsearch + Kibana**: Análisis y visualización
- **Flask API**: Servidor de consultas

### Levantar todo el sistema
docker compose up --build -d

####
Levantar módulos específicos

# Solo base de datos
docker compose up mongo mongo-express -d

# Solo scraper y dependencias
docker compose up mongo redis scraper -d

# Solo procesamiento
docker compose up filtering processing -d

##### Verificar logs

# Ver todos los logs
docker compose logs -f

# Ver logs específicos
docker compose logs -f scraper
docker compose logs -f api_server
```bash