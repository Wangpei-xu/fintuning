## fine-tuning result on LLaMA2-7B

### casual analysis on fine-tuned LLaMA2-7B

<img src="causal_llama.png" width="400" />

### detection head and target head attention pattern on (head 24, layer 9) and (head 7, layer 21)

<p>
    <img src="detection.png" width="17%">
    <img src="target.png" width="17%">
</p>

### ablation result

| **Method/Task**          | *CC1* | *CC2* | *CC4*  | *CC10* |
|--------------------------|------|------|-------|-------|
| **Baseline**             | 100  | 100  | 100 | 97.27 |
| **Detection Head Ablation** | 100  | 100  | **45.22** | **42.22** |
| **Target Head Ablation**  | 100  | 100  | **52.58** | **48.272** |
| **Combined Ablation**     | 100  | 99.15 | 41.51  | 40.12  |
| **Random Ablation**       | 99.91 | 98.02 | 99.12  | 95.20  |




## A股假阴线统计脚本

新增 `a_share_false_bearish_analysis.py`，用于统计：
- 日K出现“假阴线”（收盘价 < 开盘价，且收盘价 > 前一日收盘价）
- 下一交易日收盘价是否高于假阴线当日收盘价

示例：

```bash
pip install akshare pandas
python a_share_false_bearish_analysis.py --start 20200101 --end 20251231 --limit 300 --top 20
```
