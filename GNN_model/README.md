# 🛡️ Insure Trust AI - "Ring Hunter" GNN Module

## Overview
This folder contains the production weights (`ring_hunter_best_model.pth`) for the "**Ring Hunter**" Graph Neural Network. This module acts as our "Data Moat," specifically designed to detect organized, multi-claim insurance fraud rings that evade traditional rule-based engines.

The model is built using a **Heterogeneous Graph Attention Network (GATv2)** via PyTorch Geometric. It analyzes the structural relationships between Claimants, Doctors, Workshops, and Witnesses.

### Achievements of this Build
* **Solved the "Cold Start" Problem:** Utilizing inductive neighborhood aggregations, the model can instantly score brand-new claimants by analyzing the historical risk of their network (e.g., who they use as a doctor or witness).
* **Beating Imbalance via Focal Loss:** Standard networks fail on fraud (due to the 99% legitimate / 1% fraud ratio). This model was trained using heavily tuned Focal Loss to mathematically force the gradients to expose coordinated "Crash for Cash" rings and "Phantom Witness" loops.

---

## ⚙️ For Backend / Integration Teams

You don't need GPUs to run inference. The exported `.pth` state dictionary is pushed to CPU format. 

### Dependencies
Ensure the API microservice has the following installed:
```bash
pip install torch torch_geometric
```

### How to Load the Model for Inference

To use these weights, you must recreate the empty architecture shell and load the dictionary into it. **Do not run `to_hetero()` after loading the weights—run it before.**

```python
import torch
from torch_geometric.data import HeteroData
from torch_geometric.nn import GATv2Conv, to_hetero, Linear
import torch.nn.functional as F

# 1. Define the Core Architecture
class AdvancedFraudGNN(torch.nn.Module):
    def __init__(self, hidden_channels: int, out_channels: int, num_heads: int = 4):
        super().__init__()
        self.conv1 = GATv2Conv((-1, -1), hidden_channels, heads=num_heads, add_self_loops=False)
        self.norm1 = torch.nn.LayerNorm(hidden_channels * num_heads)
        self.conv2 = GATv2Conv((-1, -1), hidden_channels, heads=num_heads, add_self_loops=False)
        self.norm2 = torch.nn.LayerNorm(hidden_channels * num_heads)
        self.lin = Linear(hidden_channels * num_heads, out_channels)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x_out = F.leaky_relu(self.norm1(self.conv1(x, edge_index)), 0.2)
        x_out2 = F.leaky_relu(self.norm2(self.conv2(x_out, edge_index)), 0.2)
        return self.lin(x_out2)

# 2. Map the Architecture to the Database Schema
# Note: You MUST pass the exact data.metadata() from the PyG HeteroData object
# Example metadata: (['Claimant', 'Doctor', 'Workshop', 'Witness'], [('Claimant', 'Treated_By', 'Doctor')...])

base_model = AdvancedFraudGNN(hidden_channels=64, out_channels=1, num_heads=4)
production_model = to_hetero(base_model, graph_metadata, aggr='mean')

# 3. Load the Trained Weights
production_model.load_state_dict(torch.load("ring_hunter_best_model.pth", map_location=torch.device('cpu')))

# 4. Lock weights for Inference
production_model.eval()

print("✓ Ring Hunter Online: Ready to process graphs.")
```

---

## 🎨 For Frontend Teams (D3.js Visualization)

The output of this model represents an anomaly risk score per node. To render these fraud rings successfully in the UI:

1. Request the `JSON` output of the subgraph from the Backend team.
2. Load the network using `d3.forceSimulation()`.
3. Apply a dynamic rendering threshold to the `fill` or `CSS class` attributes. Example:
   ```javascript
   node.classed("fraud-pulse", d => d.risk_score > 0.85);
   ```
   *(Ensure you have a CSS keyframe setup for `.fraud-pulse` to create a glowing red effect for high-risk claimants.)*
