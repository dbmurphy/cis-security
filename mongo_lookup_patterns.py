import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# Create figure with subplots
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.3], hspace=0.3, wspace=0.2)

# Color scheme
colors = {
    'collection_a': '#FF6B6B',
    'collection_b': '#4ECDC4',
    'aggregation': '#45B7D1',
    'driver': '#96CEB4',
    'lookup': '#FFEAA7',
    'bad': '#FF7675',
    'good': '#00B894'
}

def draw_collection(ax, x, y, width, height, name, doc_count, color):
    """Draw a collection box with documents"""
    # Collection box
    rect = FancyBboxPatch((x, y), width, height, 
                         boxstyle="round,pad=0.02", 
                         facecolor=color, 
                         edgecolor='black', 
                         linewidth=2)
    ax.add_patch(rect)
    
    # Collection title
    ax.text(x + width/2, y + height - 0.1, name, 
            ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Document count
    ax.text(x + width/2, y + height - 0.25, f'{doc_count:,} documents', 
            ha='center', va='center', fontsize=10)
    
    # Draw sample documents
    doc_height = 0.08
    docs_to_show = min(5, doc_count // 100000 + 1)
    for i in range(docs_to_show):
        doc_y = y + 0.1 + i * (doc_height + 0.02)
        doc_rect = plt.Rectangle((x + 0.1, doc_y), width - 0.2, doc_height, 
                               facecolor='white', edgecolor='gray', linewidth=1)
        ax.add_patch(doc_rect)

def draw_arrow(ax, start, end, label, color='black', style='-'):
    """Draw an arrow with label"""
    arrow = ConnectionPatch(start, end, "data", "data",
                          arrowstyle="->", shrinkA=5, shrinkB=5,
                          mutation_scale=20, fc=color, ec=color, linestyle=style)
    ax.add_patch(arrow)
    
    # Add label
    mid_x, mid_y = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
    ax.text(mid_x, mid_y + 0.05, label, ha='center', va='bottom', 
            fontsize=9, fontweight='bold', color=color)

# Pattern 1: $lookup with aggregation (top row)
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 5)
ax1.set_title('Pattern 1: $lookup with Aggregation\n(Poor Performance)', 
              fontsize=14, fontweight='bold', color=colors['bad'])

# Collections
draw_collection(ax1, 0.5, 2, 2.5, 2, 'Collection A\n(Orders)', 500000, colors['collection_a'])
draw_collection(ax1, 6.5, 2, 2.5, 2, 'Collection B\n(Users)', 10000, colors['collection_b'])

# Aggregation pipeline
agg_rect = FancyBboxPatch((3.5, 0.5), 2.5, 1, 
                         boxstyle="round,pad=0.1", 
                         facecolor=colors['aggregation'], 
                         edgecolor='black', linewidth=2)
ax1.add_patch(agg_rect)
ax1.text(4.75, 1, 'Aggregation Pipeline\nwith $lookup', 
         ha='center', va='center', fontsize=10, fontweight='bold')

# Arrows
draw_arrow(ax1, (3, 3), (3.5, 1.2), '500K docs', colors['bad'])
draw_arrow(ax1, (6.5, 3), (6, 1.2), '10K docs', colors['bad'])
draw_arrow(ax1, (4.75, 0.5), (4.75, -0.5), 'Joined Result\n500K docs', colors['bad'])

ax1.axis('off')

# Pattern 2: Aggregation + Driver lookup (top right)
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 5)
ax2.set_title('Pattern 2: Aggregation + Driver Lookup\n(Good Performance)', 
              fontsize=14, fontweight='bold', color=colors['good'])

# Collections
draw_collection(ax2, 0.5, 2, 2.5, 2, 'Collection A\n(Orders)', 500000, colors['collection_a'])
draw_collection(ax2, 6.5, 2, 2.5, 2, 'Collection B\n(Users)', 10000, colors['collection_b'])

# Aggregation pipeline (only on A)
agg_rect = FancyBboxPatch((1, 0.2), 2, 0.8, 
                         boxstyle="round,pad=0.1", 
                         facecolor=colors['aggregation'], 
                         edgecolor='black', linewidth=2)
ax2.add_patch(agg_rect)
ax2.text(2, 0.6, 'Aggregation\n(group by ref)', 
         ha='center', va='center', fontsize=9, fontweight='bold')

# Driver lookup
driver_rect = FancyBboxPatch((6, 0.2), 2.5, 0.8, 
                            boxstyle="round,pad=0.1", 
                            facecolor=colors['driver'], 
                            edgecolor='black', linewidth=2)
ax2.add_patch(driver_rect)
ax2.text(7.25, 0.6, 'Driver Lookup\n(5 unique refs)', 
         ha='center', va='center', fontsize=9, fontweight='bold')

# Arrows
draw_arrow(ax2, (2, 2), (2, 1), '500K docs', colors['good'])
draw_arrow(ax2, (3, 0.6), (6, 0.6), '5 grouped\nresults', colors['good'])
draw_arrow(ax2, (7.25, 1), (7.25, 2), '5 lookups\nonly', colors['good'])

ax2.axis('off')

# Detailed flow diagrams (bottom row)
ax3 = fig.add_subplot(gs[1, :])
ax3.set_xlim(0, 20)
ax3.set_ylim(0, 8)
ax3.set_title('Detailed Performance Comparison', fontsize=14, fontweight='bold')

# Pattern 1 detailed flow
ax3.text(2.5, 7.5, 'Pattern 1: $lookup Aggregation', ha='center', va='center', 
         fontsize=12, fontweight='bold', color=colors['bad'])

steps1 = [
    (1, 6.5, '500K docs\nfrom Collection A'),
    (1, 5, 'MongoDB performs\n$lookup operation'),
    (1, 3.5, 'Joins EVERY doc\nwith Collection B'),
    (1, 2, 'Returns 500K\njoined documents'),
    (1, 0.5, 'Performance: O(N*M)\nwhere N=500K, M=10K')
]

for i, (x, y, text) in enumerate(steps1):
    rect = FancyBboxPatch((x-0.8, y-0.4), 1.6, 0.8, 
                         boxstyle="round,pad=0.05", 
                         facecolor=colors['bad'] if i == len(steps1)-1 else colors['lookup'], 
                         edgecolor='black', linewidth=1)
    ax3.add_patch(rect)
    ax3.text(x, y, text, ha='center', va='center', fontsize=9)
    
    if i < len(steps1) - 1:
        draw_arrow(ax3, (x, y-0.4), (x, steps1[i+1][1]+0.4), '', colors['bad'])

# Pattern 2 detailed flow
ax3.text(12.5, 7.5, 'Pattern 2: Aggregation + Driver Lookup', ha='center', va='center', 
         fontsize=12, fontweight='bold', color=colors['good'])

steps2 = [
    (11, 6.5, '500K docs\nfrom Collection A'),
    (11, 5, 'Aggregation groups\nby ObjectID references'),
    (11, 3.5, 'Returns only 5\nunique references'),
    (14, 3.5, 'Driver makes 5\ntargeted lookups'),
    (14, 2, 'Fetches only 5 docs\nfrom Collection B'),
    (12.5, 0.5, 'Performance: O(N) + O(K)\nwhere N=500K, K=5')
]

for i, (x, y, text) in enumerate(steps2):
    color = colors['good'] if i == len(steps2)-1 else (colors['driver'] if x > 12 else colors['aggregation'])
    rect = FancyBboxPatch((x-0.8, y-0.4), 1.6, 0.8, 
                         boxstyle="round,pad=0.05", 
                         facecolor=color, 
                         edgecolor='black', linewidth=1)
    ax3.add_patch(rect)
    ax3.text(x, y, text, ha='center', va='center', fontsize=9)
    
    if i < len(steps2) - 1:
        if i == 2:  # Arrow from aggregation to driver
            draw_arrow(ax3, (x+0.8, y), (steps2[i+1][0]-0.8, steps2[i+1][1]), '', colors['good'])
        elif i == 4:  # Arrow to final result
            draw_arrow(ax3, (x-1, y-0.4), (steps2[i+1][0], steps2[i+1][1]+0.4), '', colors['good'])
        else:
            draw_arrow(ax3, (x, y-0.4), (x, steps2[i+1][1]+0.4), '', colors['good'])

# Dividing line
ax3.axvline(x=10, color='gray', linestyle='--', alpha=0.5)

ax3.axis('off')

# Performance comparison table
ax4 = fig.add_subplot(gs[2, :])
ax4.set_xlim(0, 10)
ax4.set_ylim(0, 2)

# Table headers
headers = ['Aspect', 'Pattern 1: $lookup', 'Pattern 2: Aggregation + Driver']
col_widths = [2, 4, 4]
col_positions = [1, 3.5, 6.5]

for i, (header, pos, width) in enumerate(zip(headers, col_positions, col_widths)):
    rect = FancyBboxPatch((pos-width/2, 1.5), width, 0.4, 
                         boxstyle="round,pad=0.02", 
                         facecolor='lightgray', 
                         edgecolor='black', linewidth=1)
    ax4.add_patch(rect)
    ax4.text(pos, 1.7, header, ha='center', va='center', fontsize=10, fontweight='bold')

# Table rows
rows = [
    ['Performance', 'O(N*M) - Very Slow', 'O(N) + O(K) - Fast'],
    ['Memory Usage', 'High (500K joined docs)', 'Low (5 unique refs)'],
    ['Network Traffic', 'Heavy (large result set)', 'Light (small aggregation result)'],
    ['Best Use Case', 'Small collections only', 'Large collections with grouped refs']
]

for row_idx, row in enumerate(rows):
    y_pos = 1.1 - row_idx * 0.3
    for col_idx, (text, pos, width) in enumerate(zip(row, col_positions, col_widths)):
        color = colors['bad'] if col_idx == 1 else (colors['good'] if col_idx == 2 else 'white')
        rect = FancyBboxPatch((pos-width/2, y_pos-0.1), width, 0.2, 
                             boxstyle="round,pad=0.02", 
                             facecolor=color, 
                             edgecolor='black', linewidth=1, alpha=0.3)
        ax4.add_patch(rect)
        ax4.text(pos, y_pos, text, ha='center', va='center', fontsize=9)

ax4.axis('off')

plt.suptitle('MongoDB Collection Lookup Patterns: Performance Comparison', 
             fontsize=16, fontweight='bold', y=0.98)

plt.tight_layout()
plt.savefig('mongo_lookup_patterns.png', dpi=300, bbox_inches='tight')
plt.show()

print("Diagram saved as 'mongo_lookup_patterns.png'")
print("\nSummary:")
print("Pattern 1 ($lookup): Joins all 500K documents at database level - Poor performance")
print("Pattern 2 (Aggregation + Driver): Groups first, then lookup only unique refs - Good performance")