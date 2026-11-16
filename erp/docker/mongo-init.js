// Initialisation de MongoDB en production (exécuté une seule fois, au premier démarrage).
// Principe du moindre privilège (ADR-0004) :
//  - l'application lit `orders` (alimentée par l'ETL) et n'écrit que dans `api_orders` ;
//  - l'ETL est le seul à écrire dans `orders`.
const database = db.getSiblingDB("livraison_express");

database.createRole({
  role: "livraisonApp",
  privileges: [
    { resource: { db: "livraison_express", collection: "orders" }, actions: ["find"] },
    {
      resource: { db: "livraison_express", collection: "api_orders" },
      actions: ["find", "insert", "update", "createIndex"],
    },
  ],
  roles: [],
});

database.createUser({
  user: process.env.MONGO_APP_USERNAME,
  pwd: process.env.MONGO_APP_PASSWORD,
  roles: ["livraisonApp"],
});

database.createUser({
  user: process.env.MONGO_ETL_USERNAME,
  pwd: process.env.MONGO_ETL_PASSWORD,
  roles: [{ role: "readWrite", db: "livraison_express" }],
});
