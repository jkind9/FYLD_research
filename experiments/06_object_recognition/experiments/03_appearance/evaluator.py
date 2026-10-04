"""Independent identities join only after descriptor comparison."""

METHODS = ("zncc", "orb", "sift", "yolo")


def label_pairs(records: list[dict], pairs: list[dict]) -> list[dict]:
    lookup = {r["key"]: r for r in records}
    return [
        {
            **p,
            "same_identity": lookup[p["left"]]["identity"]
            == lookup[p["right"]]["identity"],
        }
        for p in pairs
    ]


def rank_queries(
    records: list[dict], pairs: list[dict], *, methods: tuple = METHODS
) -> list[dict]:
    scores = {frozenset((p["left"], p["right"])): p["scores"] for p in pairs}
    results = []
    for query in (r for r in records if r["partition"] == "evaluation"):
        gallery = [
            r
            for r in records
            if r["partition"] == "enrollment" and r["category"] == query["category"]
        ]
        for method in methods:
            available = [
                {
                    "key": r["key"],
                    "identity": r["identity"],
                    "score": scores[frozenset((r["key"], query["key"]))][method][
                        "score"
                    ],
                }
                for r in gallery
            ]
            available = sorted(
                (r for r in available if r["score"] is not None),
                key=lambda r: (-r["score"], r["key"]),
            )
            top = [r for r in available if available[0]["score"] - r["score"] <= 1e-6]
            identities = {r["identity"] for r in top}
            status = (
                "unavailable"
                if not top
                else "ambiguous" if len(identities) != 1 else "ranked"
            )
            assigned = next(iter(identities)) if status == "ranked" else None
            results.append(
                {
                    "query": query["key"],
                    "method": method,
                    "status": status,
                    "top_keys": [r["key"] for r in top],
                    "assigned_identity": assigned,
                    "correct": (
                        assigned == query["identity"] if assigned is not None else None
                    ),
                    "ranked_gallery": available,
                    "unavailable_gallery_count": len(gallery) - len(available),
                }
            )
    return results
