<script lang="ts">
  import { onMount } from 'svelte';

  let apiKey: string = '';
  let today = '';
  let articles: any[] = [];
  let imageArticles: any[] = [];

  function getImage(article: any): string | null {
    if (article?.multimedia?.default?.url) {
      return article.multimedia.default.url;
    } else if (article?.multimedia?.thumbnail?.url) {
      return article.multimedia.thumbnail.url;
    }
    return null;
  }

  function redirectToDex() {
    const dexURL = "http://localhost:8000/login";
    window.location.href = dexURL;
  }

  function sideBar() {
    showSideTab != showSideTab;
  }

  onMount(async () => {
    const now = new Date();
    today = now.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });

    const url = new URL(window.location.href);
    email = url.searchParams.get('user');
    

    try {
      const res = await fetch('http://localhost:8000/api/local-news');
      const data = await res.json();
      articles = data.response?.docs || [];
      imageArticles = articles.filter(article => getImage(article));
    } catch (error) {
      console.error('Failed to fetch API key:', error);
    }
  }); 
</script>

<main>
  <header>
    <div class="top-right">
      <button class="button" on:click={redirectToDex}>LOG IN</button>
    </div>
    <div class="date">
      <p><b>{today}</b><br/> Today’s Paper</p>
      <br />
    </div>
    <br>
    <div class="logo-image">
      <img src="/NYTimeslogo.png" alt="The New York Times" />
    </div>
    <hr style="margin: 1% 2% 2% 2%; width: 95%" />
  </header>

  {#if imageArticles.length > 0}
    <div class="main-container">
      <div class="left-column">
        <img src={getImage(imageArticles[2])} alt={imageArticles[2].headline.main}/>
        <h2>{imageArticles[2].headline.main}</h2>
        <p>{imageArticles[2].abstract}</p>
        <p>{imageArticles[2].lead_paragraph}</p>
        <hr style="margin: 2% 0% 10% 0%"/>

        <img src={getImage(imageArticles[3])} alt={imageArticles[3].headline.main}/>
        <h2>{imageArticles[3].headline.main}</h2>
        <p>{imageArticles[3].abstract}</p>
        <p>{imageArticles[3].lead_paragraph}</p>
      </div>

      <div class="mid-column">
        <img src={getImage(imageArticles[0])} alt={imageArticles[0].headline.main}/>
        <h1>{imageArticles[0].headline.main}</h1>
        <p>{imageArticles[0].abstract}</p>
        <p>{imageArticles[0].lead_paragraph}</p>
        <hr style="margin: 1% 0% 5% 0%"/>

        <img src={getImage(imageArticles[1])} alt={imageArticles[1].headline.main}/>
        <h3>{imageArticles[1].headline.main}</h3>
        <p>{imageArticles[1].abstract}</p>
        <p>{imageArticles[1].lead_paragraph}</p>
      </div>

      <div class="right-column">
        <img src={getImage(imageArticles[5])} alt={imageArticles[5].headline.main}/>
        <h2>{imageArticles[5].headline.main}</h2>
        <p>{imageArticles[5].abstract}</p>
        <p>{imageArticles[5].lead_paragraph}</p>
        <hr style="margin: 2% 0% 10% 0%"/>

        <img src={getImage(imageArticles[7])} alt={imageArticles[7].headline.main}/>
        <h2>{imageArticles[7].headline.main}</h2>
        <p>{imageArticles[7].abstract}</p>
        <p>{imageArticles[7].lead_paragraph}</p>
      
      </div>

      <div class="side-columns">
        <img src={getImage(imageArticles[2])} alt={imageArticles[2].headline.main}/>
        <h2>{imageArticles[2].headline.main}</h2>
        <p>{imageArticles[2].abstract}</p>
        <p>{imageArticles[2].lead_paragraph}</p>
        <hr style="margin: 5% 0% 10% 0%"/>

        <img src={getImage(imageArticles[3])} alt={imageArticles[3].headline.main}/>
        <h2>{imageArticles[3].headline.main}</h2>
        <p>{imageArticles[3].abstract}</p>
        <p>{imageArticles[3].lead_paragraph}</p>
        <hr style="margin: 5% 0% 10% 0%"/>

        <img src={getImage(imageArticles[5])} alt={imageArticles[5].headline.main}/>
        <h2>{imageArticles[5].headline.main}</h2>
        <p>{imageArticles[5].abstract}</p>
        <p>{imageArticles[5].lead_paragraph}</p>
        <hr style="margin: 5% 0% 10% 0%"/>

        <img src={getImage(imageArticles[7])} alt={imageArticles[7].headline.main}/>
        <h2>{imageArticles[7].headline.main}</h2>
        <p>{imageArticles[7].abstract}</p>
        <p>{imageArticles[7].lead_paragraph}</p>
      </div>
    </div>
  {:else}
    <p>Loading articles...</p>
  {/if}
  <hr style="height: 3px; background-color: black; margin: 2% 2% 3% 2%" />
</main>
