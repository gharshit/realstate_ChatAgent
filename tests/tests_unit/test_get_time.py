import pytest
from datetime import datetime
from app.chatagent.tools import get_current_time

@pytest.mark.asyncio
async def test_get_current_time_format():
    """Test get_current_time returns correct format."""
    result = await get_current_time.ainvoke({})
    
    assert isinstance(result, str)
    # Check format YYYY-MM-DD HH:MM:SS
    try:
        dt = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
        assert dt is not None
    except ValueError:
        pytest.fail(f"Returned time string '{result}' does not match format '%Y-%m-%d %H:%M:%S'")

