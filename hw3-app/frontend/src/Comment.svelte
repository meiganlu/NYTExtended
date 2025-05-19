<script lang="ts">
  export let c;                       
  export let articleId: string;      
  export let depth: number = 0; //nesting depth        
  export let replyOpen: Record<string, boolean>;
  export let replyBox:  Record<string, string>;

  export let doReply:  (id: string, send: boolean) => void;
  export let doDelete: (id: string) => void;

  let email: string | null = '';
  const url = new URL(window.location.href);
  email = url.searchParams.get('user');
  let isModerator = email === "moderator@hw3.com";

  if (replyBox[c.id] === undefined) replyBox[c.id] = "";

  $: stamp = new Date(c.created_at).toLocaleDateString();
</script>

<div
  class="comment {depth > 0 ? 'nested' : ''}"
  style="margin-left:{depth * 1.5}rem"
>
  <!-- ───── META ROW ──────────────────────────────────────────────── -->
  <div class="meta">
    <span class="avatar">{c.user_name?.[0]?.toUpperCase() ?? "?"}</span>
    <span class="name">{c.user_name}</span>
    <span class="time">{stamp}</span>
  </div>

  <!-- ───── BODY ──────────────────────────────────────────────────── -->
  <p class="body">{c.content}</p>
  {#if c.content !== "comment was removed by moderator"}
    <div class="actions">
      <button class="reply-link" on:click={() => doReply(c.id, false)}><strong>Reply</strong></button>
      {#if isModerator}
        <button class="del" title="Delete" on:click={() => doDelete(c.id)}><strong>Delete</strong></button>
      {/if}
    </div>
  {/if}
   

  {#if depth === 0}
    <hr />
  {/if}

  <!-- ───── ACTIONS  (reply + delete on the same row) ─────────────── -->


  <!-- ───── REPLY BOX ─────────────────────────────────────────────── -->
  {#if replyOpen[c.id]}
    <div class="reply-box">
      <textarea
        rows="2"
        bind:value={replyBox[c.id]}
        placeholder="Reply…"
      ></textarea>

      <button
        class="send"
        disabled={!replyBox[c.id]?.trim()}
        on:click={() => doReply(c.id, true)}
      >
        Send
      </button>
    </div>
  {/if}

  
  {#if c.children && c.children.length}
    {#each c.children as child (child.id)}
      <svelte:self
        c={child}
        articleId={articleId}
        depth={depth + 1}
        {replyOpen}
        {replyBox}
        {doReply}
        {doDelete}
      />
    {/each}
  {/if}
</div>


<style>
  .comment {
    font-size: .88rem;
    margin-top : 1.1rem;
    position   : relative;
  }

  .meta {
    display      : flex;
    align-items  : center;
    gap          : .4rem;
    font-size    : .75rem;
    color        : #666;
    margin-bottom: .25rem;
  }

  .avatar {
    display        : inline-flex;
    align-items    : center;
    justify-content: center;
    background     : #ccc;
    color          : #fff;
    border-radius  : 50%;
    width          : 1.2rem;
    height         : 1.2rem;
    font-size      : .7rem;
  }

  .name {
    font-weight : 700;
    color       : #000;
  }

  .time {
    font-size   : .68rem;
    margin-left : .6rem;
    
  }

  .body {
    margin : .35rem 0;
  }

  hr {
    width      : 95%;
    height     : 1px;
    border     : none;
    background : #dbdbdb;
  }



  .actions {
    display      : flex;
    align-items  : center;
    margin-top   : .15rem;
  }

  .reply-link {
    background : none;
    border     : none;
    color      : #567b95;
    font-size  : .75rem;
    cursor     : pointer;
    margin-bottom: 5%;
  }

  .reply-link:hover {
    text-decoration : underline;
  }

  .del {
    background   : none;
    border       : none;
    font-size    : .75rem;
    color        : #888;
    cursor       : pointer;
    margin-left  : auto;   /* right-aligned */
    margin-bottom: 5%;
  }

  .del:hover {
    color : #444;
  }


  .reply-box {
    display   : flex;
    gap       : .4rem;
    margin-top: .4rem;
  }

  .reply-box textarea {
    flex         : 1;
    border       : 1px solid #ccc;
    border-radius: 4px;
    padding      : .35rem;
    font-size    : .83rem;
    resize       : vertical;
  }

  .reply-box .send {
    background   : #000;
    color        : #fff;
    border       : none;
    border-radius: 4px;
    padding      : .35rem .8rem;
    font-size    : .75rem;
    cursor       : pointer;
  }

  .reply-box .send:disabled {
    background : #ccc;
    cursor     : not-allowed;
  }



  /* ─────────  threaded vertical bar for nested comments  ───────────── */

  .nested::before {
    content : "";
    position: absolute;
    top     : 0;
    left    : -.75rem;
    width   : 1px;
    height  : 100%;
    background : #d0d0d0;
  }
</style>
