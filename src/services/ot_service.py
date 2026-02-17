from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.collab_models import DocumentOperation, OpType

async def apply_operation(doc_id: int, op: DocumentOperation, session: AsyncSession) -> DocumentOperation:
    """
    Applies an operation to a document.
    """
    # Assuming 'op' is a transient ORM object or Pydantic model converted to ORM
    # If it is an ORM object (as imported), we just add it to session.

    # Check if doc exists? (omitted for brevity/focus on OT)

    op.document_id = doc_id # Ensure binding
    op.applied = True
    session.add(op)

    await session.commit()
    await session.refresh(op)
    return op

async def resolve_conflict(op1: DocumentOperation, op2: DocumentOperation) -> list[DocumentOperation]:
    """
    Resolves conflict between two operations.
    Transforms op2 against op1.
    """
    resolved_ops = []

    # Create a copy of op2 (assuming ORM object, simple copy)
    new_op = DocumentOperation(
        document_id=op2.document_id,
        user_id=op2.user_id,
        op_type=op2.op_type,
        position=op2.position,
        content=op2.content,
        timestamp=op2.timestamp,
        applied=False
    )

    # Simple OT Logic for Text
    if op1.op_type == OpType.insert and op2.op_type == OpType.insert:
        # If op1 inserted before op2, shift op2 right
        if op1.position <= op2.position:
            new_op.position += 1

    elif op1.op_type == OpType.delete and op2.op_type == OpType.insert:
        # If op1 deleted before op2, shift op2 left
        if op1.position < op2.position:
            new_op.position -= 1

    elif op1.op_type == OpType.insert and op2.op_type == OpType.delete:
        # If op1 inserted before op2's delete target, shift delete target right
        if op1.position <= op2.position:
            new_op.position += 1

    # ... more cases ...

    resolved_ops.append(new_op)
    return resolved_ops

async def get_document_state(doc_id: int, version: int, session: AsyncSession) -> str:
    """
    Reconstructs document state at a specific version.
    """
    # We fetch all operations. "version" here might map to number of ops or a snapshot.
    # Assuming version = number of applied ops for simplicity.

    stmt = select(DocumentOperation).where(
        DocumentOperation.document_id == doc_id,
        DocumentOperation.applied == True
    ).order_by(DocumentOperation.timestamp, DocumentOperation.id)

    result = await session.execute(stmt)
    ops = result.scalars().all()

    # Apply ops in order
    content = ""
    for i, op in enumerate(ops):
        # Stop if we reached the requested version
        # If version is -1, apply all. If version >= 0, apply up to `version` ops.
        if version >= 0 and i >= version:
            break

        # Interpret content
        op_content = ""
        if op.content:
            if isinstance(op.content, str):
                op_content = op.content
            elif isinstance(op.content, dict) and 'text' in op.content:
                op_content = op.content['text']
            else:
                op_content = str(op.content)

        if op.op_type == OpType.insert:
            content = content[:op.position] + op_content + content[op.position:]
        elif op.op_type == OpType.delete:
            # Delete 1 char default if content empty
            length = 1
            if op.content and isinstance(op.content, dict) and 'length' in op.content:
                length = int(op.content['length'])

            content = content[:op.position] + content[op.position + length:]

    return content
