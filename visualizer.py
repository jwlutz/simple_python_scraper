import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network
from typing import Dict, List, Any, Optional
from pathlib import Path
from crawl import normalize_url, get_domain_from_url


class SiteGraphBuilder:
    """Build a graph representation of a crawled site."""
    
    def __init__(self, page_data: Dict[str, Any], base_url: str):
        """
        Initialize the graph builder.
        
        Args:
            page_data: Dictionary of page data from crawler
            base_url: Base URL of the site
        """
        self.page_data = page_data
        self.base_url = base_url
        self.base_domain = get_domain_from_url(base_url)
        self.graph = nx.DiGraph()
        self._build_graph()
    
    def _build_graph(self):
        """Build the directed graph from page data."""
        # Add nodes for all pages
        for norm_url, data in self.page_data.items():
            if "error" in data:
                # Add error nodes with special attributes
                self.graph.add_node(
                    norm_url,
                    url=data.get("url", norm_url),
                    error=True,
                    depth=data.get("depth", 0),
                    label=self._get_label(data.get("url", norm_url))
                )
            else:
                # Add normal page nodes
                self.graph.add_node(
                    norm_url,
                    url=data["url"],
                    page_type=data.get("page_type", "unknown"),
                    depth=data.get("depth", 0),
                    incoming_link_count=data.get("incoming_link_count", 0),
                    internal_link_count=data.get("internal_link_count", 0),
                    external_link_count=data.get("external_link_count", 0),
                    response_time=data.get("response_time", 0),
                    h1=data.get("h1", ""),
                    error=False,
                    label=self._get_label(data["url"], data.get("h1", ""))
                )
        
        # Add edges for internal links
        for norm_url, data in self.page_data.items():
            if "error" not in data and "internal_links" in data:
                for link in data["internal_links"]:
                    normalized_link = normalize_url(link)
                    if normalized_link in self.graph:
                        self.graph.add_edge(norm_url, normalized_link)
    
    def _get_label(self, url: str, h1: str = "") -> str:
        """Generate a label for a node."""
        if h1:
            return f"{h1[:30]}..."if len(h1) > 30 else h1
        
        # Use the last part of the URL path
        path = url.split("/")[-1] or url.split("/")[-2] if len(url.split("/")) > 1 else url
        return path[:30] + "..." if len(path) > 30 else path or "Home"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate graph statistics."""
        if len(self.graph) == 0:
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "avg_degree": 0,
                "density": 0
            }
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "avg_in_degree": sum(d for n, d in self.graph.in_degree()) / self.graph.number_of_nodes(),
            "avg_out_degree": sum(d for n, d in self.graph.out_degree()) / self.graph.number_of_nodes(),
            "density": nx.density(self.graph),
            "is_connected": nx.is_weakly_connected(self.graph) if len(self.graph) > 0 else False
        }
    
    def generate_interactive_html(self, output_path: str, max_external_nodes: int = 50):
        """
        Generate an interactive HTML visualization using pyvis.
        
        Args:
            output_path: Path to save the HTML file
            max_external_nodes: Maximum number of external link nodes to display
        """
        net = Network(height="800px", width="100%", directed=True, notebook=False)
        net.barnes_hut(gravity=-5000, central_gravity=0.3, spring_length=100)
        
        # Color scheme
        color_by_depth = {
            0: "#1f77b4",  # Blue
            1: "#ff7f0e",  # Orange
            2: "#2ca02c",  # Green
            3: "#d62728",  # Red
            4: "#9467bd",  # Purple
        }
        error_color = "#ff0000"  # Red for errors
        
        # Add nodes
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            
            # Determine node size based on incoming links
            incoming_count = node_data.get("incoming_link_count", 0)
            size = 10 + (incoming_count * 3)  # Base size + scaling
            
            # Determine color based on depth or error status
            if node_data.get("error", False):
                color = error_color
                title = f"ERROR: {node_data.get('url', node)}"
            else:
                depth = node_data.get("depth", 0)
                color = color_by_depth.get(depth, "#999999")
                title = (
                    f"URL: {node_data.get('url', node)}\n"
                    f"Type: {node_data.get('page_type', 'unknown')}\n"
                    f"Depth: {depth}\n"
                    f"Incoming Links: {incoming_count}\n"
                    f"Internal Links: {node_data.get('internal_link_count', 0)}\n"
                    f"External Links: {node_data.get('external_link_count', 0)}\n"
                    f"Response Time: {node_data.get('response_time', 0):.2f}s"
                )
            
            net.add_node(
                node,
                label=node_data.get("label", node),
                title=title,
                color=color,
                size=size
            )
        
        # Add edges
        for edge in self.graph.edges():
            net.add_edge(edge[0], edge[1])
        
        # Save
        net.save_graph(output_path)
        print(f"Interactive graph saved to {output_path}")
    
    def generate_plotly_graph(self, output_path: str):
        """
        Generate an interactive graph using plotly.
        
        Args:
            output_path: Path to save the HTML file
        """
        if len(self.graph) == 0:
            print("No nodes to visualize")
            return
        
        # Use spring layout
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        # Create edge trace
        edge_x = []
        edge_y = []
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = self.graph.nodes[node]
            node_text.append(node_data.get("label", node))
            
            # Color by depth
            depth = node_data.get("depth", 0)
            node_color.append(depth)
            
            # Size by incoming links
            incoming = node_data.get("incoming_link_count", 0)
            node_size.append(10 + incoming * 3)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="top center",
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='Viridis',
                color=node_color,
                size=node_size,
                colorbar=dict(
                    thickness=15,
                    title='Depth',
                    xanchor='left'
                ),
                line_width=2
            )
        )
        
        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(text='Site Structure Graph', font=dict(size=16)),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )
        
        fig.write_html(output_path)
        print(f"Plotly graph saved to {output_path}")
    
    def export_graphml(self, output_path: str):
        """
        Export graph in GraphML format for use in other tools.
        
        Args:
            output_path: Path to save the GraphML file
        """
        nx.write_graphml(self.graph, output_path)
        print(f"GraphML exported to {output_path}")
    
    def get_important_pages(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most important pages based on incoming links.
        
        Args:
            top_n: Number of top pages to return
            
        Returns:
            List of page data dictionaries sorted by importance
        """
        pages_with_scores = []
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            if not node_data.get("error", False):
                pages_with_scores.append({
                    "url": node_data.get("url", node),
                    "h1": node_data.get("h1", ""),
                    "incoming_links": node_data.get("incoming_link_count", 0),
                    "depth": node_data.get("depth", 0),
                    "page_type": node_data.get("page_type", "unknown")
                })
        
        # Sort by incoming links
        pages_with_scores.sort(key=lambda x: x["incoming_links"], reverse=True)
        
        return pages_with_scores[:top_n]


def create_visualizations(page_data: Dict[str, Any], base_url: str, output_dir: str):
    """
    Create all visualizations for the crawled site.
    
    Args:
        page_data: Dictionary of page data from crawler
        base_url: Base URL of the site
        output_dir: Directory to save visualizations
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    builder = SiteGraphBuilder(page_data, base_url)
    
    # Generate interactive HTML (pyvis)
    builder.generate_interactive_html(str(output_path / "graph_interactive.html"))
    
    # Generate plotly graph
    builder.generate_plotly_graph(str(output_path / "graph_plotly.html"))
    
    # Export GraphML
    builder.export_graphml(str(output_path / "graph.graphml"))
    
    return builder

