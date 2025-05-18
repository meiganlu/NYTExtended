<script lang="ts">
  export let c;                       // comment node
  export let aid:string;              // article id
  export let depth:number = 0;        // nesting depth
  export let replyOpen:Record<string,boolean>;
  export let replyBox: Record<string,string>;

  /* handlers received from parent */
  export let doReply:(id:string,send:boolean)=>void;
  export let doDelete:(id:string)=>void;
</script>

<div class="comment" style="margin-left:{depth}rem">
  <!-- meta row -->
  <div class="meta">
    <span class="avatar">{c.user_name?.[0]?.toUpperCase() ?? '?'}</span>
    <span class="name">{c.user_name}</span>
    <span class="time">{new Date(c.created_at).toLocaleString()}</span>
    <button class="del" title="Delete" on:click={()=>doDelete(c.id)}>×</button>
  </div>

  <!-- body -->
  <p class="body">{c.content}</p>

  <!-- reply toggle -->
  <button class="reply-link" on:click={()=>doReply(c.id,false)}>Reply</button>

  <!-- reply box -->
  {#if replyOpen[c.id]}
    <div class="reply-box">
      <textarea rows="2" bind:value={replyBox[c.id]} placeholder="Reply…"/>
      <button class="send" on:click={()=>doReply(c.id,true)}>Send</button>
    </div>
  {/if}

  <!-- nested children -->
  {#if c.children && c.children.length}
    {#each c.children as child (child.id)}
      <Comment c={child} {aid}
        depth={depth+1}
        {replyOpen} {replyBox}
        {doReply} {doDelete}/>
    {/each}
  {/if}
</div>

<style>
.comment{font-size:.88rem;margin-top:1.1rem}
.meta{display:flex;align-items:center;gap:.4rem;font-size:.75rem;color:#666;margin-bottom:.25rem}
.avatar{display:inline-flex;align-items:center;justify-content:center;background:#ccc;color:#fff;
  border-radius:50%;width:1.2rem;height:1.2rem;font-size:.7rem}
.name{font-weight:700;color:#000}
.time{font-size:.68rem}
.del{margin-left:auto;background:none;border:none;font-size:1rem;line-height:1;color:#888;cursor:pointer}
.body{margin:.35rem 0}
.reply-link{background:none;border:none;color:#1158a6;font-size:.75rem;cursor:pointer}
.reply-box{display:flex;gap:.4rem;margin-top:.4rem}
.reply-box textarea{flex:1;border:1px solid #ccc;border-radius:4px;padding:.35rem;font-size:.83rem}
.reply-box .send{background:#000;color:#fff;border:none;border-radius:4px;padding:.35rem .8rem;font-size:.75rem;cursor:pointer}
</style>
