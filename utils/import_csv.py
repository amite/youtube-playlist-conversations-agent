#!/usr/bin/env python3
"""
Script to import CSV data into a pandas DataFrame and demonstrate basic operations.
"""

import pandas as pd
import os

def import_csv_to_dataframe(csv_path):
    """
    Import CSV file into a pandas DataFrame.
    
    Args:
        csv_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: DataFrame containing the CSV data
    """
    try:
        # Read CSV file into DataFrame
        df = pd.read_csv(csv_path)
        print(f"✅ Successfully imported CSV file: {csv_path}")
        print(f"📊 DataFrame shape: {df.shape}")
        print(f"📋 Columns: {list(df.columns)}")
        return df
    except FileNotFoundError:
        print(f"❌ Error: File not found at {csv_path}")
        return None
    except Exception as e:
        print(f"❌ Error importing CSV: {e}")
        return None

def analyze_dataframe(df):
    """
    Perform basic analysis on the DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame to analyze
    """
    if df is None:
        return
    
    print("\n🔍 Basic DataFrame Analysis:")
    print("\n📊 First 5 rows:")
    print(df.head())
    
    print("\n📈 Basic statistics:")
    print(df.describe())
    
    print("\n📋 Data types:")
    print(df.dtypes)
    
    print("\n🔢 Missing values:")
    print(df.isnull().sum())

def main():
    """
    Main function to demonstrate CSV import and DataFrame operations.
    """
    # Path to the CSV file
    csv_path = "data/youtube_playlist_20251219_083407.csv"
    
    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found at: {csv_path}")
        return
    
    # Import CSV to DataFrame
    df = import_csv_to_dataframe(csv_path)
    
    # Analyze the DataFrame
    analyze_dataframe(df)
    
    # Example: Filter videos with more than 10,000 views
    if df is not None:
        print(f"\n🎥 Videos with more than 10,000 views:")
        high_view_videos = df[df['video_views'] > 10000]
        print(high_view_videos[['title', 'video_views', 'video_likes']])
        
        # Example: Save processed data to new CSV
        output_path = "data/processed_youtube_data.csv"
        high_view_videos.to_csv(output_path, index=False)
        print(f"\n💾 Saved processed data to: {output_path}")

if __name__ == "__main__":
    main()