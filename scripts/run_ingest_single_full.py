import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from ingestion.ingest import DocumentIngestionPipeline
from agent.models import IngestionConfig

DOCS_DIR = r"tmp_ingest_medical"

async def main():
    pipeline = DocumentIngestionPipeline(
        config=IngestionConfig(skip_graph_building=False),
        documents_folder=DOCS_DIR,
        clean_before_ingest=True,
    )
    await pipeline.ingest_documents(tenant_slug="default")
    await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())
