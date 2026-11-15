import{request}from './client';import type{Run,SnapshotRow}from '../types/domain';export const list=()=>request<Run[]>('/runs');
export const create=(data:unknown)=>request<Run>('/runs',{method:'POST',body:JSON.stringify(data)});
export const snapshot=(id:number,group:string,offset:number,limit=100)=>request<{total:number;rows:SnapshotRow[]}>(`/runs/${id}/snapshot?group=${group}&offset=${offset}&limit=${limit}`);
