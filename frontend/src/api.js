const apiHost=window.location.hostname||'localhost';
const base=import.meta.env.VITE_API_URL||`${window.location.protocol}//${apiHost}:8000`;
export const token=()=>localStorage.getItem('token');
export async function api(path,options={}){const response=await fetch(base+'/api'+path,{...options,headers:{'Content-Type':'application/json',...(token()?{Authorization:`Bearer ${token()}`} :{}),...options.headers}});let data={};try{data=await response.json()}catch{}if(!response.ok)throw new Error(data.detail||'Something went wrong');return data}
export {base};
