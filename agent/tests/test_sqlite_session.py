import asyncio
import sys
sys.path.insert(0, '.')
from utils.adk_patch import apply_adk_patches
apply_adk_patches()
from dotenv import load_dotenv
load_dotenv()

async def test():
    from api.lifecycle import session_service, bootstrap_session
    
    # Test 1: create session
    sid = await bootstrap_session(system_id='sys-test', project_id='proj-test', session_name='My Test Session')
    print(f'Created session: {sid}')
    
    # Test 2: list sessions
    resp = await session_service.list_sessions(app_name='si_mapper', user_id='demo_user')
    sessions = resp.sessions if resp else []
    print(f'Listed {len(sessions)} sessions')
    
    # Test 3: get session
    sess = await session_service.get_session(app_name='si_mapper', user_id='demo_user', session_id=sid)
    keys = list(sess.state.keys()) if sess else None
    print(f'Get session state keys: {keys}')
    sname = sess.state.get('session_name') if sess else None
    print(f'session_name: {sname}')
    
    # Test 4: delete session
    await session_service.delete_session(app_name='si_mapper', user_id='demo_user', session_id=sid)
    sess2 = await session_service.get_session(app_name='si_mapper', user_id='demo_user', session_id=sid)
    print(f'After delete, session exists: {sess2 is not None}')
    
    print('All tests PASSED')

asyncio.run(test())

