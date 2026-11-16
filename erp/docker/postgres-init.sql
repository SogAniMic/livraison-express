-- Initialisation de la base de production simulée (ERP Pro 2015).
-- Le schéma `orders` est créé et migré par le simulateur lui-même (storage.py) :
-- ce fichier, référencé par docker-compose.erp.yml mais absent de l'archive fournie,
-- se limite à documenter la base et à poser un fuseau horaire explicite.
ALTER DATABASE livraison_express SET timezone TO 'Europe/Paris';
COMMENT ON DATABASE livraison_express IS 'Base de production ERP (simulée) - ne pas utiliser pour la Data';
