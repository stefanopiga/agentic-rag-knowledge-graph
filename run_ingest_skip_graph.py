import asyncio
from agent.models import IngestionConfig
from ingestion.ingest import DocumentIngestionPipeline

DOCS = r"documents_total\fisioterapia\master"

async def main():
    cfg = IngestionConfig(skip_graph_building=True)
    pipeline = DocumentIngestionPipeline(config=cfg, documents_folder=DOCS, clean_before_ingest=True)
    results = await pipeline.ingest_documents(tenant_slug='default')
    await pipeline.close()
    ok = sum(1 for r in results if r.success)
    total = len(results)
    print(f"INGEST_OK={ok}/{total}")

if __name__ == "__main__":
    asyncio.run(main())
