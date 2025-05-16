<script lang="ts">
  export let comment: any;
  export let articleId: string;
  export let depth: number = 0;

  export let doDelete: (id: string) => void;
  export let doReply: (id: string, send?: boolean) => void;
  export let replyOpen: Record<string, boolean>;
  export let replyBox:  Record<string, string>;
</script>

<div class="comment" style="margin-left:{depth}rem">
  <div class="meta">
    <strong>{comment.user_name}</strong>
    <span>{new Date(comment.created_at).toLocaleString()}</span>
    <button class="del" on:click={() => doDelete(comment.id)}>×</button>
  </div>

  <p class="body">{comment.content}</p>

  <button class="reply-btn" on:click={() => doReply(comment.id)}>
    {replyOpen[comment.id] ? 'Cancel' : 'Reply'}
  </button>

  {#if replyOpen[comment.id]}
    <div class="reply-box">
      <textarea rows="2" bind:value={replyBox[comment.id]} />
      <button on:click={() => doReply(comment.id, true)}>Send</button>
    </div>
  {/if}

  {#each comment.children || [] as child}
    <Comment
      comment={child}
      {articleId}
      depth={depth + 1}
      {doDelete}
      {doReply}
      {replyOpen}
      {replyBox}/>
  {/each}
</div>

<style>
  .comment   { border-left:2px solid #e5e7eb; padding-left:.75rem; margin-top:1rem; }
  .meta      { font-size:.8rem; color:#555; display:flex; gap:.5rem; align-items:center; }
  .del       { background:none; color:#c00; margin-left:auto; cursor:pointer; }
  .reply-btn { background:none; color:#0a5; margin:.25rem 0; cursor:pointer; font-size:.8rem; }
  .reply-box textarea{ width:100%; resize:vertical; padding:.3rem; border:1px solid #ccc; border-radius:.25rem; }
  .reply-box button{ margin-top:.2rem; background:#0a5; color:#fff; padding:.2rem .6rem; border:none; border-radius:.25rem; cursor:pointer; font-size:.75rem; }
</style>