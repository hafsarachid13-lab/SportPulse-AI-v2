const {createApp}=Vue;
createApp({
data(){return{
  page:'dashboard',
  dash:null,
  review:null,
  loading:false,
  genLoading:false,
  error:null,
  exportHistory:[],
  filters:{source:'',sport:'',min_credibility:0,min_importance:0},
  charts:{}
}},
async mounted(){await this.load()},
methods:{
  async load(){
    this.loading=true;this.error=null;
    try{
      const r=await axios.get('/api/v1/dashboard-data');
      this.dash=r.data;
      this.$nextTick(()=>this.drawCharts());
    }catch(e){this.error='Generate a review first to load dashboard data.'}
    finally{this.loading=false}
  },
  async genReview(){
    this.genLoading=true;
    try{
      const r=await axios.post('/api/v1/generate-review');
      this.toast('Review generated: '+r.data.total_articles+' articles','ok');
      await this.load();
      await this.loadReview();
    }catch(e){this.toast('Generation failed','err')}
    finally{this.genLoading=false}
  },
  async loadReview(){
    try{const r=await axios.get('/api/v1/review');this.review=r.data}
    catch(e){this.review=null}
  },
  async applyFilters(){
    this.loading=true;
    try{
      const p=new URLSearchParams();
      if(this.filters.source)p.append('source',this.filters.source);
      if(this.filters.sport)p.append('sport',this.filters.sport);
      p.append('min_credibility',this.filters.min_credibility);
      p.append('min_importance',this.filters.min_importance);
      const r=await axios.get('/api/v1/dashboard-data/filtered?'+p);
      this.dash=r.data;
      this.$nextTick(()=>this.drawCharts());
    }catch(e){this.toast('No articles match filters','err')}
    finally{this.loading=false}
  },
  resetFilters(){
    this.filters={source:'',sport:'',min_credibility:0,min_importance:0};
    this.load();
  },
  async doExport(fmt){
    try{
      const r=await axios.get('/api/v1/export/'+fmt);
      if(r.data.download_url){window.open(r.data.download_url,'_blank')}
      this.toast('Exported as '+fmt.toUpperCase(),'ok');
      this.loadExportHistory();
    }catch(e){this.toast('Export failed','err')}
  },
  async loadExportHistory(){
    try{const r=await axios.get('/api/v1/export/history');this.exportHistory=r.data.exports||[]}
    catch(e){}
  },
  nav(p){
    this.page=p;
    if(p==='review'&&!this.review)this.loadReview();
    if(p==='exports')this.loadExportHistory();
    if(p==='dashboard')this.$nextTick(()=>this.drawCharts());
  },
  pct(v){return(v*100).toFixed(0)+'%'},
  fmtSize(b){return b>1048576?(b/1048576).toFixed(1)+' MB':b>1024?(b/1024).toFixed(1)+' KB':b+' B'},
  drawCharts(){
    if(!this.dash)return;
    const colors=['#FF6B35','#1B9CFC','#06A77D','#F5A623','#E74C3C','#9B59B6','#3498DB','#1ABC9C'];
    // Source doughnut
    const s1=document.getElementById('srcChart');
    if(s1){
      if(this.charts.src)this.charts.src.destroy();
      this.charts.src=new Chart(s1,{type:'doughnut',data:{
        labels:this.dash.source_distribution.sources.map(s=>s.name),
        datasets:[{data:this.dash.source_distribution.sources.map(s=>s.article_count),backgroundColor:colors,borderWidth:0}]
      },options:{responsive:true,maintainAspectRatio:false,cutout:'65%',plugins:{legend:{position:'bottom',labels:{color:'#8b8fa3',padding:12,font:{size:11}}}}}});
    }
    // Sport bar
    const s2=document.getElementById('sportChart');
    if(s2){
      if(this.charts.sport)this.charts.sport.destroy();
      this.charts.sport=new Chart(s2,{type:'bar',data:{
        labels:this.dash.sport_analytics.sports.map(s=>s.sport),
        datasets:[{label:'Articles',data:this.dash.sport_analytics.sports.map(s=>s.article_count),backgroundColor:'#FF6B35',borderRadius:6,barThickness:24}]
      },options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',scales:{x:{grid:{color:'#2d3143'},ticks:{color:'#8b8fa3'}},y:{grid:{display:false},ticks:{color:'#e4e6f0',font:{weight:600}}}},plugins:{legend:{display:false}}}});
    }
    // Importance pie
    const s3=document.getElementById('impChart');
    if(s3){
      if(this.charts.imp)this.charts.imp.destroy();
      const d=this.dash.importance.distribution;
      this.charts.imp=new Chart(s3,{type:'doughnut',data:{
        labels:['High (≥70%)','Medium (40-70%)','Low (<40%)'],
        datasets:[{data:[d.high,d.medium,d.low],backgroundColor:['#06A77D','#F5A623','#E74C3C'],borderWidth:0}]
      },options:{responsive:true,maintainAspectRatio:false,cutout:'60%',plugins:{legend:{position:'bottom',labels:{color:'#8b8fa3',padding:10,font:{size:11}}}}}});
    }
    // Credibility bar
    const s4=document.getElementById('credChart');
    if(s4){
      if(this.charts.cred)this.charts.cred.destroy();
      const src=this.dash.credibility.sources_by_credibility.slice(0,8);
      this.charts.cred=new Chart(s4,{type:'bar',data:{
        labels:src.map(s=>s.source),
        datasets:[{label:'Credibility',data:src.map(s=>s.avg_credibility),backgroundColor:'#1B9CFC',borderRadius:6,barThickness:20}]
      },options:{responsive:true,maintainAspectRatio:false,scales:{x:{grid:{display:false},ticks:{color:'#8b8fa3',font:{size:10},maxRotation:45}},y:{min:0,max:1,grid:{color:'#2d3143'},ticks:{color:'#8b8fa3'}}},plugins:{legend:{display:false}}}});
    }
  },
  toast(msg,type){
    const t=document.createElement('div');t.className='toast '+type;t.textContent=msg;
    document.body.appendChild(t);setTimeout(()=>t.remove(),3500);
  }
}
}).mount('#app');
