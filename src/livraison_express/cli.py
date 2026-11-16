"""Interface en ligne de commande : les opérations qui ne sont pas des requêtes HTTP.

```bash
python -m livraison_express serve                      # démarre l'API
python -m livraison_express train                      # entraîne et sauvegarde le modèle
python -m livraison_express predict --file order.json  # prédiction locale, sans serveur
python -m livraison_express scheduler                  # réentraîne quand assez de données
```

L'entraînement est un job, pas un endpoint : un `POST /train` public permettrait à
n'importe qui de consommer le CPU du service de prédiction.
Code de sortie : 0 = succès, 1 = échec (un job en échec ne doit jamais renvoyer 0).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict
from pathlib import Path

from .domain.exceptions import LivraisonExpressError

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="livraison_express", description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="Démarrer l'API de prédiction.")
    serve.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute (%(default)s).")
    serve.add_argument("--port", type=int, default=8000, help="Port d'écoute (%(default)s).")

    commands.add_parser("train", help="Entraîner le modèle et écrire ses artefacts.")

    predict = commands.add_parser("predict", help="Prédire une commande lue dans un JSON.")
    predict.add_argument("--file", required=True, help="Fichier JSON (schéma OrderFeatures).")

    scheduler = commands.add_parser("scheduler", help="Réentraîner dès qu'assez de données.")
    scheduler.add_argument("--once", action="store_true", help="Un seul cycle puis sortie.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"serve": _serve, "train": _train, "predict": _predict, "scheduler": _scheduler}
    try:
        return handlers[args.command](args)
    except KeyboardInterrupt:
        print("Interrompu.", file=sys.stderr)
        return 1
    except LivraisonExpressError as error:
        logger.error("%s", error)
        return 1
    except Exception:
        logger.exception("Échec inattendu de la commande %s", args.command)
        return 1


def _container():
    from .core.container import Container, configure_logging

    container = Container.from_settings()
    configure_logging(container.settings.log_level)
    return container


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    from .api.app import create_app

    uvicorn.run(create_app(), host=args.host, port=args.port, proxy_headers=True)
    return 0


def _train(_: argparse.Namespace) -> int:
    started_at = time.perf_counter()
    card = _container().train_model()
    logger.info(
        "Entraînement terminé en %.2f s (%d lignes, roc_auc=%.4f)",
        time.perf_counter() - started_at,
        card.training_rows,
        card.metrics["roc_auc"],
    )
    return 0


def _predict(args: argparse.Namespace) -> int:
    from .api.schemas import OrderFeatures

    payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
    order = OrderFeatures.model_validate(payload).to_entity()
    prediction = _container().predictor().predict(order)
    print(json.dumps(asdict(prediction), ensure_ascii=False, indent=2, default=str))
    return 0


def _scheduler(args: argparse.Namespace) -> int:
    from .core.retraining import RetrainingScheduler

    scheduler = RetrainingScheduler(_container())
    scheduler.run_forever(max_iterations=1 if args.once else None)
    return 0
