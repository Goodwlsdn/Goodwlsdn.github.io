"""Explicit entry point so startup scripts can identify this API process."""
import argparse
import uvicorn

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    uvicorn.run('app:app',host='127.0.0.1',port=args.port)
