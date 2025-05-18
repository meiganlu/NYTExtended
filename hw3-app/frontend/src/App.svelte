<script lang="ts">
  import { onMount } from 'svelte';
  import Comment from './Comment.svelte';

  /* ---------- article loading ---------- */
  let today = '';
  let imageArticles: any[] = [];
  let loadError = '';

  // Auth / account drawer state
  let showAcct = false;
  let email: string | null = '';
  const loggedIn = () => !!email;          // helper

  /* ---------- comment system ---------- */
  type CommentT = {
    id: string; content: string; user_name: string;
    created_at: string; children?: CommentT[];
  };

  const comments: Record<string, CommentT[]> = {};
  const drawerOpen: Record<string, boolean> = {};
  const newTop:   Record<string, string>    = {};
  const replyOpen:Record<string, boolean>   = {};
  const replyBox: Record<string, string>    = {};

  // For showing comment counts on the home page
  let commentCounts: Record<string, number> = {};

  function getImage(a: any): string | null {
    if (a?.multimedia?.default?.url)   return a.multimedia.default.url;
    if (a?.multimedia?.thumbnail?.url) return a.multimedia.thumbnail.url;
    return null;
  }

  /* ---------- Dex helpers (UNCHANGED) ---------- */
  function redirectToDex() {
    window.location.href = 'http://localhost:8000/login';
  }

  /* ---------- lifecycle ---------- */
  onMount(async () => {
    // date
    today = new Date().toLocaleDateString('en-US',
      { weekday:'long', month:'long', day:'numeric', year:'numeric' });

    // email comes back from backend redirect (?user=…)
    const url = new URL(window.location.href);
    email = url.searchParams.get('user');

    // news
    try {
      const r = await fetch('/api/local-news', { credentials:'include' });
      const j = await r.json();
      imageArticles = (j.response?.docs || []).filter(getImage);
      
      // After loading articles, fetch comment counts for all articles
      if (imageArticles.length > 0 && loggedIn()) {
        await Promise.all(imageArticles.map(async (article) => {
          if (article._id) {
            await fetchCommentCount(article._id);
          }
        }));
      }
      
      // Check for any article ID in localStorage to pre-load comments
      const lastOpenDrawer = localStorage.getItem('openArticleDrawer');
      if (lastOpenDrawer && loggedIn()) {
        drawerOpen[lastOpenDrawer] = true;
        await fetchComments(lastOpenDrawer);
      }
    } catch (e) {
      loadError = 'Could not load news.';
      console.error(e);
    }
  });

  /* ---------- comments CRUD ---------- */
  async function fetchCommentCount(aid: string) {
    try {
      const safe = encodeURIComponent(aid);
      const r = await fetch(`/api/comments/${safe}`, { credentials:'include' });
      
      if (r.ok) {
        const commentsData = await r.json();
        // Count total comments (including nested ones)
        const countNestedComments = (comments: any[]): number => {
          let count = comments.length;
          for (const comment of comments) {
            if (comment.children && comment.children.length) {
              count += countNestedComments(comment.children);
            }
          }
          return count;
        };
        
        commentCounts[aid] = countNestedComments(commentsData);
      }
    } catch (error) {
      console.error(`Failed to fetch comment count for ${aid}:`, error);
      commentCounts[aid] = 0;
    }
  }
  
  async function fetchComments(aid: string) {
    try {
      const safe = encodeURIComponent(aid);
      const r = await fetch(`/api/comments/${safe}`, { credentials:'include' });
      
      if (r.ok) {
        const commentsData = await r.json();
        comments[aid] = commentsData;
        
        // Update comment count as well
        const countNestedComments = (comments: any[]): number => {
          let count = comments.length;
          for (const comment of comments) {
            if (comment.children && comment.children.length) {
              count += countNestedComments(comment.children);
            }
          }
          return count;
        };
        
        commentCounts[aid] = countNestedComments(commentsData);
      } else {
        console.error(`Error fetching comments: ${r.status}`);
        comments[aid] = []; 
        commentCounts[aid] = 0;
      }
    } catch (error) {
      console.error('Failed to fetch comments:', error);
      comments[aid] = []; 
      commentCounts[aid] = 0;
    }
  }
  
  async function post(aid: string, parentId: string | null, text: string) {
    if (!loggedIn() || !text.trim()) return;
    try {
      const safe = encodeURIComponent(aid);
      const r = await fetch(`/api/comments/${safe}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ 
          content: text.trim(), 
          parent_id: parentId 
        }),
        credentials: 'include'
      });
      
      if (r.ok) {
        // Clear the input field
        if (parentId) {
          replyBox[parentId] = '';
          // Close reply form after successful post
          replyOpen[parentId] = false;
        } else {
          newTop[aid] = '';
        }
        
        // Refresh comments
        await fetchComments(aid);
      } else {
        console.error(`Error posting comment: ${r.status}`);
        alert('Failed to post comment. Please try again.');
      }
    } catch (error) {
      console.error('Failed to post comment:', error);
      alert('Failed to post comment. Please try again.');
    }
  }
  
  async function handleDelete(cid: string, aid: string) {
    if (!confirm('Delete this comment?')) return;
    try {
      const r = await fetch(`/api/comments/${cid}`, { 
        method: 'DELETE', 
        credentials: 'include' 
      });
      
      if (r.ok) {
        await fetchComments(aid);
      } else {
        console.error(`Error deleting comment: ${r.status}`);
        alert('Failed to delete comment. Please try again.');
      }
    } catch (error) {
      console.error('Failed to delete comment:', error);
      alert('Failed to delete comment. Please try again.');
    }
  }
  
  function handleReply(aid: string, cid: string, send = false) {
    if (send) {
      post(aid, cid, replyBox[cid]);
    } else {
      // Toggle reply form visibility
      replyOpen[cid] = !replyOpen[cid];
      // Initialize reply box if not already set
      if (!replyBox[cid]) {
        replyBox[cid] = '';
      }
    }
  }

  /* ---------- drawer helpers ---------- */
  function openDrawer(aid: string) {
    if (!loggedIn()) return;          // gate: only logged-in users
    
    // Close any other open drawers first
    Object.keys(drawerOpen).forEach(key => {
      if (drawerOpen[key] && key !== aid) {
        drawerOpen[key] = false;
      }
    });
    
    drawerOpen[aid] = true;
    
    // Store the open drawer ID in localStorage
    localStorage.setItem('openArticleDrawer', aid);
    
    // Fetch comments if not already loaded
    if (!comments[aid]) {
      fetchComments(aid);
    }
  }
  
  function closeDrawer(aid: string) {
    drawerOpen[aid] = false;
    
    // Clear the stored drawer ID when closing
    localStorage.removeItem('openArticleDrawer');
  }
</script>

<main>
  <!-- ───── Header ───── -->
  <header class="site-header">
    <div class="date">
      <p><b>{today}</b><br/>Today's Paper</p>
    </div>

    <img class="logo" src="/NYTimeslogo.png" alt="The New York Times" />

    <div class="top-right">
      {#if !loggedIn()}
        <button class="button" on:click={redirectToDex}>Log in</button>
      {:else}
        <button class="acct-btn" on:click={() => showAcct = true}>Account</button>
      {/if}
    </div>
  </header>

  <!-- ───── Account drawer ───── -->
  {#if showAcct}
    <div class="overlay" on:click={() => showAcct = false}></div>
    <aside class="acct-drawer">
      <button class="close" on:click={() => showAcct = false}>×</button>
      <p class="acct-email"><b>{email}</b></p>
      <p class="greeting">Good&nbsp;afternoon.</p>
      <button class="logout" on:click={() => window.location.href='/logout'}>Log&nbsp;out</button>
    </aside>
  {/if}

  <!-- ───── Body ───── -->
  {#if loadError}
    <p class="err">{loadError}</p>
  {:else if !imageArticles.length}
    <p class="loading">Loading articles…</p>
  {:else}
    <div class="main-container">
      <!-- left -->
      <div class="left-column">
        {#each [2,3] as idx}
          {#if imageArticles[idx]}
            {@const art=imageArticles[idx]}
            <article class="card">
              <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)} />
              <h2>{art.headline.main}</h2>
              <p>{art.abstract}</p>
              <button class="count-btn" on:click={() => openDrawer(art._id)}>
                💬 {commentCounts[art._id] || 0}
              </button>
            </article>
          {/if}
        {/each}
      </div>

      <!-- mid -->
      <div class="mid-column">
        {#if imageArticles[0]}
          {@const art=imageArticles[0]}
          <article class="card lead">
            <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)} />
            <h1>{art.headline.main}</h1>
            <p>{art.abstract}</p>
            <button class="count-btn" on:click={() => openDrawer(art._id)}>
              💬 {commentCounts[art._id] || 0}
            </button>
          </article>
        {/if}

        {#if imageArticles[1]}
          {@const art=imageArticles[1]}
          <article class="card medium">
            <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)} />
            <h3>{art.headline.main}</h3>
            <p>{art.abstract}</p>
            <button class="count-btn" on:click={() => openDrawer(art._id)}>
              💬 {commentCounts[art._id] || 0}
            </button>
          </article>
        {/if}
      </div>

      <!-- right -->
      <div class="right-column">
        {#each [5,7] as idx}
          {#if imageArticles[idx]}
            {@const art=imageArticles[idx]}
            <article class="card">
              <img src={getImage(art)} alt={art.headline.main} on:click={() => openDrawer(art._id)} />
              <h2>{art.headline.main}</h2>
              <p>{art.abstract}</p>
              <button class="count-btn" on:click={() => openDrawer(art._id)}>
                💬 {commentCounts[art._id] || 0}
              </button>
            </article>
          {/if}
        {/each}
      </div>
    </div>
  {/if}

  <!-- ───── Comment drawers ───── -->
  {#each Object.keys(drawerOpen) as aid (aid)}
    {#if drawerOpen[aid]}
      <div class="overlay" on:click={() => closeDrawer(aid)}></div>
      <aside class="drawer">
        <button class="close" on:click={() => closeDrawer(aid)}>×</button>
        <h2>{imageArticles.find(a=>a._id===aid)?.headline?.main || 'Comments'} ({commentCounts[aid] || 0})</h2>

        <div class="new-box">
          <textarea
            rows="2"
            bind:value={newTop[aid]}
            placeholder="Add a public comment…"
            disabled={!loggedIn()}>
          </textarea>
          <button
            class="post"
            disabled={!loggedIn() || !newTop[aid]?.trim()}
            on:click={() => post(aid,null,newTop[aid])}>
            Post
          </button>
        </div>

        {#if comments[aid]?.length}
          {#each comments[aid] as c (c.id)}
            <Comment
              {c}
              articleId={aid}
              depth={0}
              doDelete={(id)=>handleDelete(id,aid)}
              doReply={(id,send)=>handleReply(aid,id,send)}
              {replyOpen} {replyBox} />
          {/each}
        {:else}
          <p class="none">No comments yet</p>
        {/if}
      </aside>
    {/if}
  {/each}
</main>