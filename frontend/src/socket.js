import {io} from 'socket.io-client';
import {base,token} from './api';
let socket;
export function connectSocket(){if(!socket)socket=io(base,{auth:{token:token()},autoConnect:false});if(!socket.connected){socket.auth={token:token()};socket.connect()}return socket}
export function disconnectSocket(){socket?.disconnect();socket=null}
