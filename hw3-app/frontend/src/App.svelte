<script lang="ts">
  import { onMount } from 'svelte';
  import Comment       from './Comment.svelte';

  /* ─── app state ─────────────────────────────────────────────────── */
  let today            = '';
  let imageArticles:any[] = [];
  let loadError        = '';

  /*  dex / account state  */
  let isAuthenticated  = false;
  let email:string|null= null;
  let showAccountTab   = false;

  /*  per-article comment state (same as before)  */
  type CommentT = { id:string; content:string; user_name:string;
                    created_at:string; children?:CommentT[] };
  const comments:Record<string,CommentT[]> = {};
  const drawerOpen:Record<string,boolean>  = {};
  const newTop:Record<string,string>       = {};
  const replyOpen:Record<string,boolean>   = {};
  const replyBox:Record<string,string>     = {};

  /* ─── helpers ───────────────────────────────────────────────────── */
  function getImage(a:any):string|null{
    return a?.multimedia?.default?.url
        ?? a?.multimedia?.thumbnail?.url
        ?? null;
  }
  const redirectToDex = () =>
    window.location.href = 'http://localhost:8000/login';

  const toggleAccount = () => showAccountTab = !showAccountTab;

  /* ─── lifecycle ─────────────────────────────────────────────────── */
  onMount(async ()=>{
    /* date */
    today = new Date().toLocaleDateString('en-US',
      { weekday:'long', month:'long', day:'numeric', year:'numeric' });

    /* dex callback?  read ?user=email@example.com */
    const url = new URL(window.location.href);
    email = url.searchParams.get('user');
    isAuthenticated = !!email;

    /* news */
    try{
      const r = await fetch('/api/local-news',{credentials:'include'});
      const j = await r.json();
      imageArticles = (j.response?.docs||[]).filter(getImage);
    }catch(e){ loadError = 'Could not load news.'; console.error(e); }
  });

  /* ─── comment api calls  (same as before, credentials:include) ─── */
  async function fetchComments(aid:string){
    const safe = encodeURIComponent(aid);
    const r = await fetch(`/api/comments/${safe}`,{credentials:'include'});
    comments[aid] = await r.json();
  }
  async function post(aid:string,pid:string|null,txt:string){
    if(!txt.trim()) return;
    await fetch(`/api/comments/${encodeURIComponent(aid)}`,{
      method:'POST',credentials:'include',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({content:txt.trim(),parent_id:pid})
    });
    if(pid) replyBox[pid]=''; else newTop[aid]='';
    fetchComments(aid);
  }
  async function del(cid:string,aid:string){
    await fetch(`/api/comments/${cid}`,{method:'DELETE',credentials:'include'});
    fetchComments(aid);
  }
  const reply = (aid:string,cid:string,send=false)=>{
    if(send) post(aid,cid,replyBox[cid]);
    else replyOpen[cid]=!replyOpen[cid];
  };
  const openDrawer  = (aid:string)=>{ drawerOpen[aid]=true; fetchComments(aid); };
  const closeDrawer = (aid:string)=>{ drawerOpen[aid]=false; };
</script>

<main>
  <!-- ─── header ─────────────────────────────────────────────────── -->
  <header class="site-header">
    <!-- login / account on the very right -->
    <div class="top-right">
      {#if !isAuthenticated}
        <button class="button" on:click={redirectToDex}>LOG&nbsp;IN</button>
      {:else}
        <button class="button" on:click={toggleAccount}>Account</button>
      {/if}
    </div>

    <!-- date on the left (CSS positions it) -->
    <div class="date"><p><b>{today}</b><br/>Today’s Paper</p></div>

    <!-- NYT logo -->
    <img src="/NYTimeslogo.png" alt="The New York Times" class="logo"/>
  </header>

  <!-- account panel -->
  {#if showAccountTab}
    <aside class="sidebar">
      <h3>Signed in</h3>
      <p>{email}</p>
      <button class="button" on:click={()=>window.location.href='/logout'}>Logout</button>
    </aside>
  {/if}

  <!-- ─── content grid / comments (identical to earlier build) ─── -->
  {#if loadError}<p class="err">{loadError}</p>
  {:else if !imageArticles.length}<p class="loading">Loading articles…</p>
  {:else}
    <div class="main-container">
      <!-- LEFT -->
      <div class="left-column">
        {#each [2,3] as i}{#if imageArticles[i]}
          {@const art=imageArticles[i]}
          <article class="card small">
            <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)}/>
            <h2>{art.headline.main}</h2><p>{art.abstract}</p>
            <button class="count-btn" on:click={()=>openDrawer(art._id)}>
              💬 {comments[art._id]?.length||0}
            </button>
          </article>{/if}{/each}
      </div>

      <!-- MID -->
      <div class="mid-column">
        {#if imageArticles[0]}{@const art=imageArticles[0]}
          <article class="card lead">
            <img src={getImage(art)} alt={art.headline.main} on:click={()=>openDrawer(art._id)}/>
            <h1>{art.headline.main}</h1><p>{art.abstract}</p>
            <button class="count-btn" on:click={()=>openDrawer(art._id)}>
              💬 {comments[art._id]?.length||0}
            </button>
          </article>{/if}

        {#if imageArticles[1]}{@const art=imageArticles[1]}
          <article class="card medium">
            <img src={getImage(art)} alt={art.headline.main} on:click={()=>openDrawer(art._id)}/>
            <h3>{art.headline.main}</h3><p>{art.abstract}</p>
            <button class="count-btn" on:click={()=>openDrawer(art._id)}>
              💬 {comments[art._id]?.length||0}
            </button>
          </article>{/if}
      </div>

      <!-- RIGHT -->
      <div class="right-column">
        {#each [5,7] as i}{#if imageArticles[i]}
          {@const art=imageArticles[i]}
          <article class="card small">
            <img src={getImage(art)} alt={art.headline.main} on:click={()=>openDrawer(art._id)}/>
            <h2>{art.headline.main}</h2><p>{art.abstract}</p>
            <button class="count-btn" on:click={()=>openDrawer(art._id)}>
              💬 {comments[art._id]?.length||0}
            </button>
          </article>{/if}{/each}
      </div>
    </div>
  {/if}

  <!-- comment drawers (unchanged) -->
  {#each Object.keys(drawerOpen) as aid (aid)}
    {#if drawerOpen[aid]}
      <div class="overlay" on:click={()=>closeDrawer(aid)}/>
      <aside class="drawer">
        <button class="close" on:click={()=>closeDrawer(aid)}>×</button>
        <h2>Comments ({comments[aid]?.length||0})</h2>

        <textarea rows="3" bind:value={newTop[aid]} placeholder="Share your thoughts…"/>
        <button class="post" on:click={()=>post(aid,null,newTop[aid])}>Post</button>

        {#if comments[aid]?.length}
          {#each comments[aid] as c (c.id)}
            <Comment comment={c} articleId={aid} depth={0}
                     doDelete={(id)=>del(id,aid)}
                     doReply ={(id,send)=>reply(aid,id,send)}
                     {replyOpen} {replyBox}/>
          {/each}
        {:else}
          <p class="none">No comments yet</p>
        {/if}
      </aside>
    {/if}
  {/each}
</main>
