import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
# Force offline embeddings and skip graph
os.environ.setdefault("EMBEDDINGS_OFFLINE", "1")

from ingestion.ingest import DocumentIngestionPipeline
from agent.models import IngestionConfig

async def main():
    pipeline = DocumentIngestionPipeline(
        config=IngestionConfig(skip_graph_building=True),
        documents_folder=r"documents_total\fisioterapia\master",
        clean_before_ingest=True,
    )
    await pipeline.ingest_documents(tenant_slug="default")
    await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())
