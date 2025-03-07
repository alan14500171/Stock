var e=(e,t,a)=>new Promise(((l,s)=>{var d=e=>{try{n(a.next(e))}catch(t){s(t)}},o=e=>{try{n(a.throw(e))}catch(t){s(t)}},n=e=>e.done?l(e.value):Promise.resolve(e.value).then(d,o);n((a=a.apply(e,t)).next())}));import{G as t,r as a,o as l,$ as s,e as d,f as o,g as n,h as i,i as r,w as u,j as c,v as m,C as b,F as v,D as p,t as h,A as y,a as f}from"./vendor-BeeV2Y_X.js";import{_ as g}from"./index-CkM21um_.js";const w={class:"container-fluid py-3"},k={class:"card"},_={class:"card-body border-bottom"},x={class:"col-md-3"},E={class:"col-md-3"},C={class:"col-md-3"},M={class:"card-body"},L={class:"table-responsive","data-testid":"holder-table-container"},I={class:"table table-bordered table-hover"},U=["data-testid"],V=["data-testid"],B=["onClick","data-testid"],T=["onClick","disabled","data-testid"],j={key:0},D={key:0,class:"card-body text-center py-5 position-absolute top-0 start-0 w-100 h-100 bg-white bg-opacity-75","data-testid":"loading-indicator"},q={class:"modal fade",id:"holderModal",tabindex:"-1","aria-hidden":"true","data-testid":"holder-modal"},S={class:"modal-dialog"},$={class:"modal-content"},A={class:"modal-header"},O={class:"modal-title","data-testid":"modal-title"},P={class:"modal-body"},F={class:"mb-3"},G={class:"mb-3"},H={class:"mb-3"},R=["value"],z={class:"mb-3"},J={class:"text-end"},K=["disabled"],N={class:"modal fade",id:"deleteModal",tabindex:"-1","aria-hidden":"true","data-testid":"delete-modal"},Q={class:"modal-dialog"},W={class:"modal-content"},X={class:"modal-body"},Y={"data-testid":"delete-confirmation-message"},Z={class:"modal-footer"},ee=["disabled"],te=g({__name:"Holder",setup(g){const te=t(),ae=a([]),le=a([]),se=a(!1),de=a(!1),oe=a(!1),ne=a(!1),ie=a(null);let re=null,ue=null;const ce=a({name:"",type:"",status:""}),me=a({name:"",type:"individual",user_id:"",status:1}),be=()=>{try{const e=document.getElementById("holderModal"),t=document.getElementById("deleteModal");if(e){const t=bootstrap.Modal.getInstance(e);t&&t.dispose(),re=new bootstrap.Modal(e,{backdrop:"static",keyboard:!1})}if(t){const e=bootstrap.Modal.getInstance(t);e&&e.dispose(),ue=new bootstrap.Modal(t,{backdrop:"static",keyboard:!1})}}catch(e){}},ve=()=>{document.querySelectorAll(".modal-backdrop").forEach((e=>{e.classList.remove("show"),setTimeout((()=>{e.remove()}),150)})),document.body.classList.remove("modal-open"),document.body.style.overflow="",document.body.style.paddingRight=""},pe=()=>e(this,null,(function*(){se.value=!0;try{const e=yield f.get("/api/holders");e.data.success?(ae.value=e.data.data,ae.value.forEach((e=>{}))):te.error("加载持有人列表失败: "+e.data.message)}catch(e){te.error("加载持有人列表失败，请稍后重试")}finally{se.value=!1}})),he=()=>e(this,null,(function*(){try{const e=yield f.get("/api/system/user/available");e.data.success&&(le.value=e.data.data,le.value.forEach((e=>{})))}catch(e){te.error("加载可用用户列表失败，请稍后重试")}})),ye=()=>{ce.value={name:"",type:"",status:""},pe()},fe=()=>{ne.value=!1,me.value={name:"",type:"individual",user_id:"",status:1},re?re.show():(be(),setTimeout((()=>{re?re.show():te.error("打开模态框失败，请刷新页面重试")}),100))},ge=()=>e(this,null,(function*(){var e,t;if(me.value.name){de.value=!0;try{let e;e=ne.value?yield f.put(`/api/holders/${me.value.id}`,me.value):yield f.post("/api/holders",me.value),e.data.success?(te.success(e.data.message||(ne.value?"更新持有人成功":"添加持有人成功")),_e(),pe()):te.error(e.data.message||"操作失败")}catch(a){te.error((null==(t=null==(e=a.response)?void 0:e.data)?void 0:t.message)||"保存失败，请稍后重试")}finally{de.value=!1}}else te.warning("请输入持有人姓名")})),we=()=>e(this,null,(function*(){var e,t;if(ie.value){oe.value=!0;try{const e=yield f.delete(`/api/holders/${ie.value.id}`);e.data.success?(te.success(e.data.message||"删除持有人成功"),xe(),pe()):te.error(e.data.message||"删除失败")}catch(a){te.error((null==(t=null==(e=a.response)?void 0:e.data)?void 0:t.message)||"删除失败，请稍后重试")}finally{oe.value=!1}}})),ke=()=>{be()};l((()=>{pe(),he(),setTimeout((()=>{be()}),500),window.addEventListener("load",ke),document.addEventListener("DOMContentLoaded",ke);const e=document.getElementById("holderModal");e&&e.addEventListener("hidden.bs.modal",(()=>{ve()}));const t=document.getElementById("deleteModal");t&&t.addEventListener("hidden.bs.modal",(()=>{ve()}))})),s((()=>{window.removeEventListener("load",ke),document.removeEventListener("DOMContentLoaded",ke);const e=document.getElementById("holderModal");e&&e.removeEventListener("hidden.bs.modal",ve);const t=document.getElementById("deleteModal");t&&t.removeEventListener("hidden.bs.modal",ve)}));const _e=()=>{re&&(re.hide(),ve())},xe=()=>{ue&&(ue.hide(),ve())};return(e,t)=>{var a;return o(),d("div",w,[n("div",k,[n("div",{class:"card-header d-flex justify-content-between align-items-center"},[t[8]||(t[8]=n("h4",{class:"mb-0","data-testid":"holder-title"},"持有人管理",-1)),n("button",{class:"btn btn-primary",onClick:fe,"data-testid":"add-holder-btn"},t[7]||(t[7]=[n("i",{class:"bi bi-plus-circle"},null,-1),r(" 添加持有人 ")]))]),n("div",_,[n("form",{onSubmit:u(pe,["prevent"]),class:"row g-3 align-items-end","data-testid":"search-form"},[n("div",x,[t[9]||(t[9]=n("label",{class:"form-label","data-testid":"holder-name-label"},"持有人姓名",-1)),c(n("input",{type:"text",class:"form-control","onUpdate:modelValue":t[0]||(t[0]=e=>ce.value.name=e),placeholder:"输入持有人姓名","data-testid":"holder-name-input"},null,512),[[m,ce.value.name]])]),n("div",E,[t[11]||(t[11]=n("label",{class:"form-label","data-testid":"holder-type-label"},"类型",-1)),c(n("select",{class:"form-select","onUpdate:modelValue":t[1]||(t[1]=e=>ce.value.type=e),"data-testid":"holder-type-select"},t[10]||(t[10]=[n("option",{value:""},"全部",-1),n("option",{value:"individual"},"个人",-1),n("option",{value:"institution"},"机构",-1)]),512),[[b,ce.value.type]])]),n("div",C,[t[13]||(t[13]=n("label",{class:"form-label","data-testid":"holder-status-label"},"状态",-1)),c(n("select",{class:"form-select","onUpdate:modelValue":t[2]||(t[2]=e=>ce.value.status=e),"data-testid":"holder-status-select"},t[12]||(t[12]=[n("option",{value:""},"全部",-1),n("option",{value:"1"},"启用",-1),n("option",{value:"0"},"禁用",-1)]),512),[[b,ce.value.status]])]),n("div",{class:"col-md-3"},[t[15]||(t[15]=n("button",{class:"btn btn-primary me-2",type:"submit","data-testid":"search-btn"},[n("i",{class:"bi bi-search"}),r(" 查询 ")],-1)),n("button",{class:"btn btn-secondary",type:"button",onClick:ye,"data-testid":"reset-btn"},t[14]||(t[14]=[n("i",{class:"bi bi-arrow-counterclockwise"},null,-1),r(" 重置 ")]))])],32)]),n("div",M,[n("div",L,[n("table",I,[t[17]||(t[17]=n("thead",null,[n("tr",null,[n("th",{style:{width:"60px"}},"ID"),n("th",null,"持有人姓名"),n("th",null,"类型"),n("th",null,"关联用户"),n("th",null,"状态"),n("th",null,"创建时间"),n("th",null,"更新时间"),n("th",{style:{width:"150px"}},"操作")])],-1)),n("tbody",null,[(o(!0),d(v,null,p(ae.value,(e=>(o(),d("tr",{key:e.id,"data-testid":"holder-row-"+e.id},[n("td",null,h(e.id),1),n("td",null,h(e.name),1),n("td",null,h("individual"===e.type?"个人":"机构"),1),n("td",null,h(e.username||"未关联"),1),n("td",null,[n("span",{class:y(1===e.status?"badge bg-success":"badge bg-danger"),"data-testid":"holder-status-badge-"+e.id},h(1===e.status?"启用":"禁用"),11,V)]),n("td",null,h(e.created_at),1),n("td",null,h(e.updated_at),1),n("td",null,[n("button",{class:"btn btn-sm btn-info me-1",onClick:t=>(e=>{ne.value=!0,me.value={id:e.id,name:e.name,type:e.type,user_id:e.user_id||"",status:e.status},e.user_id&&e.username&&(le.value.some((t=>t.id===e.user_id))||le.value.push({id:e.user_id,username:e.username,display_name:e.user_display_name}));re?re.show():(be(),setTimeout((()=>{re?re.show():te.error("打开编辑模态框失败，请刷新页面重试")}),100))})(e),"data-testid":"edit-holder-btn-"+e.id}," 编辑 ",8,B),n("button",{class:"btn btn-sm btn-danger",onClick:t=>(e=>{ie.value=e,ue?ue.show():(be(),setTimeout((()=>{ue?ue.show():te.error("打开删除确认模态框失败，请刷新页面重试")}),100))})(e),disabled:se.value,"data-testid":"delete-holder-btn-"+e.id}," 删除 ",8,T)])],8,U)))),128)),0===ae.value.length?(o(),d("tr",j,t[16]||(t[16]=[n("td",{colspan:"8",class:"text-center py-3","data-testid":"no-data-message"},"暂无数据",-1)]))):i("",!0)])])])]),se.value?(o(),d("div",D,t[18]||(t[18]=[n("div",{class:"spinner-border text-primary",role:"status"},[n("span",{class:"visually-hidden"},"加载中...")],-1),n("p",{class:"mt-2"},"加载数据中，请稍候...",-1)]))):i("",!0)]),n("div",q,[n("div",S,[n("div",$,[n("div",A,[n("h5",O,h(ne.value?"编辑持有人":"添加持有人"),1),n("button",{type:"button",class:"btn-close",onClick:_e,"aria-label":"Close","data-testid":"close-modal-btn"})]),n("div",P,[n("form",{onSubmit:u(ge,["prevent"]),"data-testid":"holder-form"},[n("div",F,[t[19]||(t[19]=n("label",{class:"form-label","data-testid":"holder-name-form-label"},[r("持有人姓名 "),n("span",{class:"text-danger"},"*")],-1)),c(n("input",{type:"text",class:"form-control","onUpdate:modelValue":t[3]||(t[3]=e=>me.value.name=e),required:"",placeholder:"请输入持有人姓名","data-testid":"holder-name-form-input",id:"holder-name"},null,512),[[m,me.value.name]])]),n("div",G,[t[21]||(t[21]=n("label",{class:"form-label","data-testid":"holder-type-form-label"},[r("类型 "),n("span",{class:"text-danger"},"*")],-1)),c(n("select",{class:"form-select","onUpdate:modelValue":t[4]||(t[4]=e=>me.value.type=e),required:"","data-testid":"holder-type-form-select",id:"holder-type"},t[20]||(t[20]=[n("option",{value:"individual"},"个人",-1),n("option",{value:"institution"},"机构",-1)]),512),[[b,me.value.type]])]),n("div",H,[t[23]||(t[23]=n("label",{class:"form-label","data-testid":"holder-user-form-label"},"关联用户",-1)),c(n("select",{class:"form-select","onUpdate:modelValue":t[5]||(t[5]=e=>me.value.user_id=e),"data-testid":"holder-user-form-select",id:"holder-user"},[t[22]||(t[22]=n("option",{value:""},"不关联用户",-1)),(o(!0),d(v,null,p(le.value,(e=>(o(),d("option",{key:e.id,value:e.id},h(e.username),9,R)))),128))],512),[[b,me.value.user_id]])]),n("div",z,[t[25]||(t[25]=n("label",{class:"form-label","data-testid":"holder-status-form-label"},"状态",-1)),c(n("select",{class:"form-select","onUpdate:modelValue":t[6]||(t[6]=e=>me.value.status=e),"data-testid":"holder-status-form-select",id:"holder-status"},t[24]||(t[24]=[n("option",{value:1},"启用",-1),n("option",{value:0},"禁用",-1)]),512),[[b,me.value.status]])]),n("div",J,[n("button",{type:"button",class:"btn btn-secondary me-2",onClick:_e,"data-testid":"cancel-form-btn"}," 取消 "),n("button",{type:"submit",class:"btn btn-primary",disabled:de.value,"data-testid":"save-holder-btn"},h(de.value?"保存中...":"保存"),9,K)])],32)])])])]),n("div",N,[n("div",Q,[n("div",W,[n("div",{class:"modal-header"},[t[26]||(t[26]=n("h5",{class:"modal-title","data-testid":"delete-modal-title"},"确认删除",-1)),n("button",{type:"button",class:"btn-close",onClick:xe,"aria-label":"Close","data-testid":"close-delete-modal-btn"})]),n("div",X,[n("p",Y,[t[27]||(t[27]=r("确定要删除持有人 ")),n("strong",null,h(null==(a=ie.value)?void 0:a.name),1),t[28]||(t[28]=r(" 吗？"))]),t[29]||(t[29]=n("p",{class:"text-danger","data-testid":"delete-warning"},"注意：如果该持有人已被交易记录引用，将只会被禁用而非删除。",-1))]),n("div",Z,[n("button",{type:"button",class:"btn btn-secondary",onClick:xe,"data-testid":"cancel-delete-btn"},"取消"),n("button",{type:"button",class:"btn btn-danger",onClick:we,disabled:oe.value,"data-testid":"confirm-delete-btn"},h(oe.value?"删除中...":"确认删除"),9,ee)])])])])])}}},[["__scopeId","data-v-87703f69"]]);export{te as default};
