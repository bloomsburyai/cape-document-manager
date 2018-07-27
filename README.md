# cape_document_manager [![CircleCI](https://circleci.com/gh/bloomsburyai/cape-document-manager.svg?style=svg&circle-token=8bdf5acf18af32ddb5fc14b9c15edf2a64d1e52a)](https://circleci.com/gh/bloomsburyai/cape-document-manager)

This implementation is meant to demonstrate how to integrate a document manager with retrieval in your existing infrastructure.
In a nutshell, it serves as a document DB leveraging fulltext indexing.

## Integration options

To integrate into your existing production infrastructure, you have 2 options:

   * **Faster to implement**, DB independent : Implement the interface provided by `Retriever` in  [document_manager_core.py](https://github.com/bloomsburyai/cape-document-manager/blob/master/cape_document_manager/document_manager_core.py)
   * Slower to implement, **optimized for your storage** : Implement the interface provided by annotation and document stores in [annotation_store.py](https://github.com/bloomsburyai/cape-document-manager/blob/master/cape_document_manager/annotation_store.py) and [document_store.py](https://github.com/bloomsburyai/cape-document-manager/blob/master/cape_document_manager/document_store.py)

