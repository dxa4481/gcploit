
async function init(){
    const response = await fetch('/nodes.json');
    const nodes = await response.json();
    const response2 = await fetch('/edges.json');
    const edges = await response2.json();
    const response3 = await fetch('/innocent_edges.json');
    const innocent_edges = await response3.json();



    var cy = cytoscape({
      container: document.getElementById('cy'),

      boxSelectionEnabled: false,
      autounselectify: true,

      style: cytoscape.stylesheet()
        .selector('node')
          .style({
            'content': 'data(id)'
          })
        .selector('edge')
          .style({
            'curve-style': 'bezier',
    //        'style': {
                "label": "data(label)",
    //        },
            'target-arrow-shape': 'triangle',
            'width': 4,
            'line-color': '#ddd',
            'target-arrow-color': '#ddd'
          })
        .selector('.highlighted')
          .style({
            'background-color': '#61bffc',
            'line-color': '#61bffc',
            'width': 20,
            'target-arrow-color': '#61bffc',
            'transition-property': 'background-color, line-color, target-arrow-color',
            'transition-duration': '0.5s'
          })
        .selector('node[type="project"]')
          .style({
            'background-color': 'red',
            'shape': 'triangle'
          })
        .selector('node[type="serviceAccount"]')
          .style({
            'background-color': 'blue',
            'shape': 'square'
          })
        .selector('node[type="userAccount"]')
          .style({
            'background-color': 'green',
            'shape': 'circle'
          }),

      elements: {
          nodes: nodes,
          edges: edges
        },

      layout: {
        name: 'cose',
        directed: true,
        roots: '#a',
        padding: 10,
        nodeRepulsion: 90000070500,
        gravity: 0,
        edgeElasticity: 0.99
      }
    });

    var bfs = cy.elements().bfs(id='#14', function(v, e, u, i, depth){
    }, true);

    var highlightNextEle = function(){
      var i = 0;
      while( i < bfs.path.length ){
        bfs.path[i].addClass('highlighted');
        i++;
      }
      innocent_edges.forEach(function(value, index, array){
        cy.add([{"group": "edges", "data": value["data"]}]);
      })
    };

    // kick off first highlight
    document.addEventListener('keyup', logKey);
    document.cy = cy;

    function logKey(e) {
        highlightNextEle();
    }
}
init();
