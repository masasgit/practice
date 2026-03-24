import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image

st.title('streamlit test')

st.write('dataframe')
st.write('Display image')

option = st.selectbox(
    'which number do you like?',
    list(range(1, 10))
)

'The number you like is ', option, '.'

if st.checkbox('show image'):
    img = Image.open('終了しました.png')
    st.image(img, caption='終了しました', use_column_width=True)

df = pd.DataFrame({
    '1列目': [1,2,3,4],
    '2列目': [10, 20, 30, 40],

})

st.write(df)

st.dataframe(df.style.highlight_max(axis=0), width=500, height=300)
#dataframeだけが表の仕様を設定できる。Writeではできない

st.table(df.style.highlight_max(axis=0))
#tableの場合は静的なテーブル。dataframeは動的なテーブルを出せる。

"""
# 章
## 節
### 項

```python
import streamlit as st
import numpy as np
import pandas as pd
```
"""

df = pd.DataFrame(
    np.random.rand(20, 3),
    columns=['a', 'b', 'c']
)
df
st.line_chart(df)
st.area_chart(df)
st.bar_chart(df)

df = pd.DataFrame(
    np.random.rand(100, 2)/[50, 50] + [35.69, 139.70],
    columns=['lat', 'lon']
)
df

st.map(df)

st.write('Interactive widgets')

left_column, right_column = st.columns(2)
button = left_column.button('Show caracter in right column')
if button:
    right_column.write('This is a right column')

expander = st.expander('Contact')
expander.write('Write a contents of contact')

text = st.text_input('What is your hobby?')
'Your hobby is ', text, '.'

condition = st.slider('What feeling do you have now?', 0, 100, 50)
'Your condition : ', condition