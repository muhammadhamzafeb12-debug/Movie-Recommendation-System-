import streamlit as st
from training import recommend, new_df

# Streamlit app setup
st.title('Movie Recommender System')

# User input for movie title
option = st.selectbox(
    "Select Movie",
    (new_df["title"].values),
)

if st.button('Recommend'):
    if option in new_df['title'].values:
        st.write(f"Recommendations for {option}:")
        # Get recommendations and display them
        recommendations = recommend(option)
        if recommendations:
            for rec in recommendations:
                st.write(rec)
    else:
        st.write("Movie not found, please try another movie.")
