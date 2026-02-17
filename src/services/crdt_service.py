from typing import List, Optional
from pydantic import BaseModel
import difflib

class DocumentOperation(BaseModel):
    op_type: str  # 'insert' or 'delete'
    position: int
    content: Optional[str] = None
    length: Optional[int] = None
    user_id: Optional[str] = None

class Op(BaseModel):
    type: str
    pos: int
    content: Optional[str] = None
    len: Optional[int] = None

class CRDTService:
    async def merge_concurrent_edits(self, ops: List[DocumentOperation]) -> List[DocumentOperation]:
        """
        Merge concurrent edits using a CRDT-inspired approach or Operational Transformation logic.
        This is a simplified mock implementation.
        """
        # In a real implementation, we would check for conflicts, reorder operations,
        # or transform indices based on other operations.
        # For now, we return the operations as they are, assuming casual ordering is handled by the caller.
        return ops

    async def generate_diff(self, old_state: str, new_state: str) -> List[Op]:
        """
        Generate a list of operations (diff) to transform old_state to new_state.
        """
        matcher = difflib.SequenceMatcher(None, old_state, new_state)
        diff_ops = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                diff_ops.append(Op(type='delete', pos=i1, len=i2-i1))
                diff_ops.append(Op(type='insert', pos=i1, content=new_state[j1:j2]))
            elif tag == 'delete':
                diff_ops.append(Op(type='delete', pos=i1, len=i2-i1))
            elif tag == 'insert':
                diff_ops.append(Op(type='insert', pos=i1, content=new_state[j1:j2]))
            # 'equal' is ignored
        return diff_ops

crdt_service = CRDTService()
