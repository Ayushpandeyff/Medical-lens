# enhanced_medical_misinformation_app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import pickle
import os
import glob
import warnings
from datetime import datetime
import requests
import zipfile
from io import BytesIO
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class MedicalMisinformationDetector:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=20000,  # Increased for better medical term coverage
            stop_words='english', 
            ngram_range=(1, 4),  # Extended n-grams for medical phrases
            min_df=2,
            max_df=0.95,
            sublinear_tf=True  # Better for text classification
        )
        
        # Enhanced ensemble model for better accuracy
        self.lr_model = LogisticRegression(max_iter=3000, C=1.0, class_weight='balanced')
        self.rf_model = RandomForestClassifier(n_estimators=150, random_state=42, class_weight='balanced')
        self.model = VotingClassifier(
            estimators=[('lr', self.lr_model), ('rf', self.rf_model)],
            voting='soft'
        )
        
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        self.is_trained = False
        self.training_info = {}
        
        # Expanded medical terms for comprehensive health misinformation detection
        self.medical_terms = {
            'diseases': [
                'covid', 'coronavirus', 'cancer', 'diabetes', 'hypertension', 'heart disease',
                'stroke', 'alzheimer', 'parkinson', 'arthritis', 'asthma', 'depression',
                'anxiety', 'hiv', 'aids', 'tuberculosis', 'malaria', 'influenza', 'pneumonia',
                'bronchitis', 'hepatitis', 'kidney disease', 'liver disease', 'obesity',
                'anemia', 'leukemia', 'lymphoma', 'melanoma', 'osteoporosis', 'fibromyalgia',
                'migraine', 'epilepsy', 'multiple sclerosis', 'lupus', 'psoriasis', 'eczema',
                'jaundice', 'appendicitis', 'gallstones', 'ulcer', 'gastritis', 'ibs',
                'crohn', 'colitis', 'diverticulitis', 'hemorrhoids', 'constipation',
                'diarrhea', 'nausea', 'vomiting', 'fever', 'cough', 'cold', 'flu'
            ],
            'treatments': [
                'vaccine', 'vaccination', 'medicine', 'medication', 'drug', 'pill', 'tablet',
                'injection', 'surgery', 'operation', 'therapy', 'treatment', 'cure', 'remedy',
                'antibiotic', 'antiviral', 'painkiller', 'aspirin', 'ibuprofen', 'acetaminophen',
                'insulin', 'chemotherapy', 'radiation', 'dialysis', 'transplant', 'implant',
                'prosthetic', 'bandage', 'cast', 'splint', 'physiotherapy', 'rehabilitation',
                'acupuncture', 'massage', 'exercise', 'diet', 'nutrition', 'supplement',
                'vitamin', 'mineral', 'protein', 'carbohydrate', 'fiber', 'antioxidant'
            ],
            'medical_professionals': [
                'doctor', 'physician', 'surgeon', 'nurse', 'therapist', 'pharmacist',
                'dentist', 'optometrist', 'psychiatrist', 'psychologist', 'cardiologist',
                'neurologist', 'oncologist', 'dermatologist', 'pediatrician', 'gynecologist',
                'urologist', 'orthopedist', 'radiologist', 'anesthesiologist', 'pathologist',
                'specialist', 'consultant', 'practitioner', 'clinician', 'paramedic'
            ],
            'medical_facilities': [
                'hospital', 'clinic', 'emergency room', 'pharmacy', 'laboratory', 'radiology',
                'intensive care', 'icu', 'operating room', 'ward', 'ambulance', 'medical center',
                'health center', 'urgent care', 'walk-in clinic', 'outpatient', 'inpatient'
            ],
            'misinformation_indicators': [
                'miracle', 'instant', 'guaranteed', 'secret', 'hidden', 'conspiracy',
                'big pharma', 'natural cure', 'detox', 'cleanse', 'superfood', 'breakthrough',
                'revolutionary', 'amazing', 'incredible', 'shocking', 'they dont want you to know',
                'doctors hate', 'industry secret', 'ancient remedy', 'forbidden',
                'alternative medicine', 'homeopathy', 'naturopathy', 'essential oils',
                'crystals', 'energy healing', 'alkaline', 'toxins', 'chemicals'
            ],
            'scientific_terms': [
                'clinical trial', 'peer review', 'randomized', 'placebo', 'double blind',
                'meta analysis', 'systematic review', 'evidence based', 'fda approved',
                'who approved', 'research', 'study', 'scientist', 'medical journal',
                'pubmed', 'cochrane', 'systematic', 'statistical', 'significant'
            ]
        }
        
        # Dataset download URLs and information
        self.dataset_sources = {
            'fakehealth': {
                'description': 'Comprehensive fake health news dataset',
                'url': 'https://github.com/EnyanDai/FakeHealth',
                'files': ['HealthStory.csv', 'HealthRelease.csv']
            },
            'coaid': {
                'description': 'COVID-19 healthcare misinformation dataset',
                'url': 'https://github.com/cuilimeng/CoAID',
                'files': ['05-28-2020/FinalDataset/NewsFakeCOVID-19.csv', 
                         '05-28-2020/FinalDataset/NewsRealCOVID-19.csv']
            }
        }

    def create_comprehensive_medical_dataset(self):
        """Create a comprehensive medical misinformation dataset with examples covering various conditions"""
        print("Creating comprehensive medical misinformation dataset...")
        
        fake_medical_claims = [
            # COVID-19 related
            "COVID-19 vaccines contain microchips for government tracking and mind control",
            "Drinking bleach or disinfectant cures coronavirus infection completely",
            "5G towers spread coronavirus through electromagnetic radiation waves",
            "Face masks reduce oxygen levels and cause carbon dioxide poisoning",
            "Natural immunity from herbs is better than COVID-19 vaccination",
            
            # Cancer misinformation
            "Ginger can completely cure cancer without any medical treatment needed",
            "Cancer is caused by negative thoughts and emotions, positive thinking cures it",
            "Baking soda injections can cure any type of cancer in days",
            "Doctors hide cancer cures to make money from chemotherapy treatments",
            "Essential oils can replace chemotherapy and radiation treatments for cancer",
            
            # Diabetes misinformation
            "Cinnamon supplements can completely cure type 1 diabetes naturally",
            "Diabetics can stop taking insulin by drinking okra water daily",
            "Type 2 diabetes is not a real disease, just pharmaceutical marketing",
            "Bitter melon extract eliminates need for diabetes medication forever",
            "Diabetes can be cured by going on a 30-day water fast",
            
            # Heart disease misinformation
            "Heart attacks can be prevented by coughing vigorously during symptoms",
            "Coconut oil prevents and reverses all forms of heart disease",
            "Cholesterol medications are unnecessary, lemon water clears arteries",
            "Heart disease is caused by vitamin C deficiency, not cholesterol",
            "Aspirin therapy for heart disease causes more harm than benefits",
            
            # Vaccine misinformation
            "All vaccines cause autism and developmental disorders in children",
            "Vaccines contain mercury and aluminum that poison the brain",
            "Natural infection is always better than vaccination for immunity",
            "Vaccine ingredients include aborted fetal tissue and animal DNA",
            "Vaccines are designed to control population growth and fertility",
            
            # Mental health misinformation
            "Depression is just laziness and lack of willpower, not medical condition",
            "Antidepressants are addictive and cause more problems than they solve",
            "Mental illness can be cured by positive thinking and exercise alone",
            "Therapy is useless, people just need to toughen up mentally",
            "ADHD is not real, children just need more discipline and structure",
            
            # General medical misinformation
            "Antibiotics can treat viral infections like cold and flu",
            "Natural supplements are always safer than prescription medications",
            "Detox diets and cleanses remove toxins that doctors can't detect",
            "Alkaline water prevents and cures all diseases by balancing pH",
            "Homeopathic remedies are scientifically proven to cure serious diseases",
            
            # Specific condition misinformation
            "Arthritis pain can be cured by wearing copper bracelets",
            "Kidney stones can be dissolved by drinking apple cider vinegar",
            "High blood pressure can be cured by eating garlic daily",
            "Asthma inhalers are dangerous, breathing exercises cure asthma completely",
            "Jaundice can be cured by drinking only sugarcane juice for weeks",
            
            # Diet and nutrition misinformation
            "Carbohydrates are toxic and should never be consumed by humans",
            "Drinking your own urine cures all diseases and promotes longevity",
            "Raw food diets prevent and cure all forms of cancer",
            "Gluten causes autism and should be avoided by everyone",
            "Intermittent fasting can cure type 1 diabetes and autoimmune diseases"
        ]
        
        real_medical_information = [
            # COVID-19 facts
            "COVID-19 vaccines have been shown to be effective in preventing severe illness",
            "Wearing masks helps reduce transmission of respiratory droplets containing virus",
            "Social distancing measures help slow the spread of coronavirus infections",
            "Medical researchers continue studying COVID-19 treatment options through clinical trials",
            "Vaccination programs are being implemented globally by health authorities",
            
            # Cancer facts
            "Cancer treatment typically involves surgery, chemotherapy, or radiation therapy",
            "Early detection through screening improves cancer treatment outcomes significantly",
            "Oncologists work with patients to develop personalized treatment plans",
            "Clinical trials test new cancer treatments for safety and effectiveness",
            "Cancer prevention includes healthy lifestyle choices and avoiding carcinogens",
            
            # Diabetes facts
            "Type 1 diabetes requires insulin therapy for blood sugar management",
            "Type 2 diabetes can be managed through medication, diet, and exercise",
            "Regular blood glucose monitoring helps diabetes patients control their condition",
            "Diabetes complications can be prevented through proper medical management",
            "Dietary changes and weight management help control type 2 diabetes",
            
            # Heart disease facts
            "Heart disease is treated through medications, lifestyle changes, and procedures",
            "Regular exercise and healthy diet reduce risk of cardiovascular disease",
            "Cholesterol management is important for heart disease prevention",
            "Cardiologists specialize in diagnosing and treating heart conditions",
            "Blood pressure medication helps prevent stroke and heart attacks",
            
            # Vaccine facts
            "Vaccines undergo rigorous safety testing before approval for public use",
            "Immunization programs have eliminated or reduced many infectious diseases",
            "Vaccine side effects are typically mild and temporary",
            "Healthcare providers monitor vaccine safety through surveillance systems",
            "Vaccines protect both individuals and communities through herd immunity",
            
            # Mental health facts
            "Mental health conditions are medical disorders that require professional treatment",
            "Therapy and medication can effectively treat depression and anxiety disorders",
            "Mental health professionals provide evidence-based treatments for patients",
            "Early intervention improves outcomes for mental health conditions",
            "Mental health is an important component of overall health and wellbeing",
            
            # General medical facts
            "Antibiotics are effective against bacterial infections but not viral infections",
            "Prescription medications undergo clinical trials to test safety and efficacy",
            "Medical treatments are based on scientific evidence and clinical research",
            "Healthcare providers use evidence-based medicine to treat patients",
            "Regular medical checkups help detect and prevent health problems",
            
            # Specific condition facts
            "Arthritis is managed through medication, physical therapy, and lifestyle modifications",
            "Kidney stones can be treated through medication, procedures, or surgery",
            "High blood pressure is controlled through medication and lifestyle changes",
            "Asthma is managed with bronchodilators and anti-inflammatory medications",
            "Jaundice requires medical evaluation to determine underlying cause and treatment",
            
            # Diet and nutrition facts
            "Balanced diets include variety of foods from all major food groups",
            "Nutritional supplements should complement, not replace, healthy eating habits",
            "Registered dietitians provide evidence-based nutrition counseling to patients",
            "Medical nutrition therapy helps manage chronic diseases like diabetes",
            "Dietary modifications can be part of comprehensive treatment plans"
        ]
        
        # Combine all examples
        all_texts = fake_medical_claims + real_medical_information
        all_labels = [0] * len(fake_medical_claims) + [1] * len(real_medical_information)
        
        df = pd.DataFrame({
            'text': all_texts,
            'label': all_labels,
            'source_file': 'comprehensive_medical_dataset'
        })
        
        return df.sample(frac=1, random_state=42).reset_index(drop=True)

    def discover_datasets(self):
        """Discover and analyze all CSV, Excel, TSV, and JSON files in datasets folder"""
        datasets_info = []
        
        # Look for datasets in multiple possible locations - now includes TSV and JSON
        search_patterns = [
            'datasets/*.csv', 'datasets/*.xlsx', 'datasets/*.xls', 'datasets/*.tsv', 'datasets/*.json', 'datasets/*.jsonl',
            'data/*.csv', 'data/*.xlsx', 'data/*.xls', 'data/*.tsv', 'data/*.json', 'data/*.jsonl',
            '*.csv', '*.xlsx', '*.xls', '*.tsv', '*.json', '*.jsonl'
        ]
        
        dataset_files = []
        for pattern in search_patterns:
            dataset_files.extend(glob.glob(pattern))
        
        dataset_files = list(set(dataset_files))  # Remove duplicates
        
        print(f"Found {len(dataset_files)} potential dataset files (CSV, Excel, TSV, JSON):")
        
        for file_path in dataset_files:
            try:
                file_extension = os.path.splitext(file_path)[1].lower()
                
                # Read sample based on file type
                if file_extension == '.csv':
                    df_sample = pd.read_csv(file_path, nrows=5)
                    df_full = pd.read_csv(file_path)
                elif file_extension in ['.xlsx', '.xls']:
                    df_sample = pd.read_excel(file_path, nrows=5)
                    df_full = pd.read_excel(file_path)
                elif file_extension == '.tsv':
                    # Handle TSV files (Tab-separated values)
                    df_sample = pd.read_csv(file_path, sep='\t', nrows=5)
                    df_full = pd.read_csv(file_path, sep='\t')
                elif file_extension in ['.json', '.jsonl']:
                    # Handle JSON files
                    try:
                        if file_extension == '.json':
                            df_full = pd.read_json(file_path)
                        else:  # .jsonl
                            df_full = pd.read_json(file_path, lines=True)
                        df_sample = df_full.head(5)
                    except Exception as json_error:
                        print(f"Error reading JSON {file_path}: {json_error}")
                        continue
                else:
                    continue
                
                file_info = {
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'file_type': file_extension,
                    'columns': list(df_sample.columns),
                    'shape': df_full.shape,
                    'text_columns': [],
                    'label_columns': [],
                    'usable': False,
                    'medical_score': 0
                }
                
                # Identify text columns
                for col in df_sample.columns:
                    col_lower = col.lower()
                    if any(term in col_lower for term in ['title', 'text', 'content', 'news', 'claim', 'article', 'statement', 'headline', 'body', 'description']):
                        file_info['text_columns'].append(col)
                
                # Identify label columns
                for col in df_sample.columns:
                    col_lower = col.lower()
                    if any(term in col_lower for term in ['label', 'fake', 'real', 'true', 'false', 'target', 'class', 'verdict', 'rating', 'category']):
                        file_info['label_columns'].append(col)
                        unique_vals = df_full[col].unique()
                        file_info[f'{col}_unique_values'] = list(unique_vals)
                
                # Calculate medical relevance score - IMPROVED
                if file_info['text_columns']:
                    # Use multiple columns and more samples for better scoring
                    sample_texts = []
                    for text_col in file_info['text_columns'][:2]:  # Check up to 2 text columns
                        sample_data = df_sample[text_col].astype(str).head(10)  # More samples
                        sample_texts.extend(sample_data.tolist())
                    
                    combined_text = ' '.join(sample_texts).lower()
                    
                    # Enhanced medical term detection
                    medical_score = 0
                    for category, term_list in self.medical_terms.items():
                        for term in term_list:
                            if term in combined_text:
                                medical_score += 1
                    
                    # Also check for health-related keywords that might not be in our lists
                    health_keywords = ['health', 'medical', 'disease', 'treatment', 'patient', 'clinical', 'hospital', 'doctor', 'medicine', 'diagnosis', 'symptom', 'therapy', 'healthcare', 'pharmaceutical', 'epidemic', 'pandemic', 'virus', 'bacteria', 'infection', 'prevention', 'wellness']
                    for keyword in health_keywords:
                        if keyword in combined_text:
                            medical_score += 2  # Higher weight for obvious health terms
                    
                    file_info['medical_score'] = medical_score
                    
                    # For PUBHEALTH-style datasets, boost score if filename suggests health content
                    filename_lower = file_info['file_name'].lower()
                    if any(word in filename_lower for word in ['health', 'medical', 'pubhealth', 'fact', 'claim']):
                        file_info['medical_score'] += 10  # Significant boost
                        print(f"Boosted medical score for health-related filename: {file_info['file_name']}")
                
                # Mark as usable if we have both text and label columns
                if file_info['text_columns'] and file_info['label_columns']:
                    file_info['usable'] = True
                
                datasets_info.append(file_info)
                usability = "✓ Usable" if file_info['usable'] else "✗ Not usable"
                medical_relevance = f"Medical Score: {file_info['medical_score']}"
                print(f"{usability} - {file_info['file_name']}: {file_info['shape']} - {medical_relevance}")
                
            except Exception as e:
                print(f"✗ Error analyzing {file_path}: {e}")
                continue
        
        return datasets_info

    def preprocess_text(self, text):
        """Enhanced text preprocessing for medical content"""
        if not isinstance(text, str) or pd.isna(text):
            return ""

        text = str(text).lower()

        # Remove URLs, emails, social media handles, and HTML tags
        text = re.sub(r'http\S+|www\S+|https\S+|@\w+|#\w+|\S+@\S+|<[^>]+>', '', text)
        
        # Preserve medical terms and dosages (e.g., "5mg", "100ml")
        text = re.sub(r'(\d+)\s*(mg|ml|g|kg|lb|oz|mcg|iu)', r'\1\2', text)
        
        # Remove special characters but keep medical punctuation
        text = re.sub(r'[^a-zA-Z\s.,!?0-9/-]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Tokenize and process
        words = text.split()
        
        # Enhanced stopwords removal with medical term preservation
        processed_words = []
        for word in words:
            if len(word) > 2:
                # Preserve medical terms even if they're in stopwords
                is_medical_term = any(word in term_list for term_list in self.medical_terms.values())
                if is_medical_term or word not in self.stop_words:
                    # Don't stem medical terms to preserve accuracy
                    if is_medical_term:
                        processed_words.append(word)
                    else:
                        stemmed_word = self.stemmer.stem(word)
                        processed_words.append(stemmed_word)
        
        return ' '.join(processed_words)

    def load_and_process_datasets(self):
        """Load, combine, and process all available datasets"""
        datasets_info = self.discover_datasets()
        usable_datasets = [d for d in datasets_info if d['usable']]
        
        if not usable_datasets:
            print("No external datasets found. Using comprehensive medical dataset...")
            return self.create_comprehensive_medical_dataset()
        
        print(f"\nProcessing {len(usable_datasets)} usable datasets...")
        
        all_dataframes = []
        
        # Always include our comprehensive medical dataset
        comprehensive_df = self.create_comprehensive_medical_dataset()
        all_dataframes.append(comprehensive_df)
        print(f"Added comprehensive medical dataset: {len(comprehensive_df)} samples")
        
        # Process external datasets
        for dataset_info in usable_datasets:
            try:
                print(f"\nProcessing: {dataset_info['file_name']} (Medical Score: {dataset_info['medical_score']})")
                
                file_extension = dataset_info['file_type']
                
                # Load file based on type
                if file_extension == '.csv':
                    df = pd.read_csv(dataset_info['file_path'])
                elif file_extension in ['.xlsx', '.xls']:
                    df = pd.read_excel(dataset_info['file_path'])
                elif file_extension == '.tsv':
                    df = pd.read_csv(dataset_info['file_path'], sep='\t')
                elif file_extension in ['.json', '.jsonl']:
                    if file_extension == '.json':
                        df = pd.read_json(dataset_info['file_path'])
                    else:  # .jsonl
                        df = pd.read_json(dataset_info['file_path'], lines=True)
                else:
                    continue
                
                # Select best text and label columns
                text_col = dataset_info['text_columns'][0]
                label_col = dataset_info['label_columns'][0]
                
                processed_df = pd.DataFrame()
                processed_df['text'] = df[text_col].astype(str)
                processed_df['label'] = df[label_col]
                processed_df['source_file'] = dataset_info['file_name']
                
                # Standardize labels
                unique_labels = processed_df['label'].unique()
                print(f"Found labels: {unique_labels}")
                
                if len(unique_labels) >= 2:  # Accept 2 or more labels now
                    label_mapping = self.determine_label_mapping(unique_labels, dataset_info['file_name'])
                    
                    # Apply mapping and keep only mapped labels
                    processed_df['original_label'] = processed_df['label']
                    processed_df['label'] = processed_df['label'].map(label_mapping)
                    
                    # Remove unmapped labels (NaN values)
                    before_count = len(processed_df)
                    processed_df = processed_df.dropna(subset=['label'])
                    after_count = len(processed_df)
                    
                    if before_count != after_count:
                        print(f"Filtered out {before_count - after_count} unmapped labels")
                    
                    # Ensure we still have both classes
                    remaining_labels = processed_df['label'].unique()
                    if len(remaining_labels) < 2:
                        print(f"Skipping {dataset_info['file_name']} - Only one label class after mapping")
                        continue
                        
                else:
                    print(f"Skipping {dataset_info['file_name']} - Less than 2 unique labels")
                    continue
                
                # Clean and filter data
                processed_df = processed_df.dropna()
                processed_df = processed_df[processed_df['text'].str.len() > 10]  # Reduced minimum length
                processed_df = processed_df.drop_duplicates(subset=['text'])
                
                print(f"After cleaning: {len(processed_df)} samples")
                
                # REMOVED overly restrictive medical filtering - keep all health-related data
                # The old code was filtering out too much data based on medical terms
                # Now we trust that PUBHEALTH and similar datasets ARE medical by nature
                
                if len(processed_df) > 0:
                    print(f"✅ Added {len(processed_df)} samples from {dataset_info['file_name']}")
                    all_dataframes.append(processed_df)
                else:
                    print(f"❌ No samples left after processing {dataset_info['file_name']}")
                
            except Exception as e:
                print(f"Error processing {dataset_info['file_name']}: {e}")
                continue
        
        if not all_dataframes:
            return self.create_comprehensive_medical_dataset()
        
        # Combine all datasets
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Report statistics
        fake_count = len(combined_df[combined_df['label'] == 0])
        real_count = len(combined_df[combined_df['label'] == 1])
        
        print(f"\nFinal combined dataset: {len(combined_df)} total samples")
        print(f"Misinformation: {fake_count} samples")
        print(f"Legitimate info: {real_count} samples")
        
        # Balance dataset if heavily skewed (but be less aggressive)
        if fake_count > 0 and real_count > 0:  # Make sure we have both classes
            ratio = max(fake_count, real_count) / min(fake_count, real_count)
            if ratio > 5:  # Only balance if extremely skewed (was 3, now 5)
                print(f"Dataset heavily skewed (ratio: {ratio:.1f}), balancing...")
                min_count = min(fake_count, real_count)
                max_samples = min(min_count * 3, max(fake_count, real_count))  # Allow up to 3:1 ratio
                
                fake_df = combined_df[combined_df['label'] == 0].sample(
                    min(fake_count, max_samples), random_state=42
                )
                real_df = combined_df[combined_df['label'] == 1].sample(
                    min(real_count, max_samples), random_state=42
                )
                combined_df = pd.concat([fake_df, real_df], ignore_index=True)
                print(f"Balanced dataset: {len(combined_df)} samples (fake: {len(fake_df)}, real: {len(real_df)})")
            else:
                print(f"Dataset ratio acceptable ({ratio:.1f}), keeping all samples")
        
        return combined_df.sample(frac=1, random_state=42).reset_index(drop=True)

    def determine_label_mapping(self, unique_labels, filename):
        """Intelligently determine label mappings for various datasets"""
        labels = [str(label).lower() for label in unique_labels]
        
        fake_indicators = ['fake', 'false', '0', 'no', 'unreliable', 'misleading', 'misinformation', 'myth', 'hoax']
        real_indicators = ['real', 'true', '1', 'yes', 'reliable', 'factual', 'legitimate', 'fact', 'verified']
        
        mapping = {}
        
        # Handle multi-label datasets (like PUBHEALTH)
        if len(unique_labels) > 2:
            print(f"Multi-label dataset detected: {unique_labels}")
            
            # For PUBHEALTH-style datasets: true=1, false=0, others=skip or group
            for original_label in unique_labels:
                label_str = str(original_label).lower()
                
                if 'true' in label_str or 'factual' in label_str:
                    mapping[original_label] = 1  # Real
                elif 'false' in label_str or 'fake' in label_str:
                    mapping[original_label] = 0  # Fake
                elif 'mixture' in label_str or 'mostly' in label_str:
                    # Mixed claims - classify as misinformation for safety
                    mapping[original_label] = 0  # Fake
                elif 'unproven' in label_str or 'disputed' in label_str:
                    # Unproven claims - classify as misinformation for safety  
                    mapping[original_label] = 0  # Fake
                else:
                    # Default fallback
                    mapping[original_label] = 0 if 'fake' in filename.lower() else 1
            
            print(f"Multi-label mapping: {mapping}")
            return mapping
        
        # Handle binary datasets (your COVID data)
        for original_label in unique_labels:
            label_str = str(original_label).lower()
            
            if any(indicator in label_str for indicator in fake_indicators):
                mapping[original_label] = 0
            elif any(indicator in label_str for indicator in real_indicators):
                mapping[original_label] = 1
            else:
                # Default mapping
                mapping[original_label] = 0 if original_label == unique_labels[0] else 1
        
        print(f"Binary label mapping for {filename}: {mapping}")
        return mapping

    def analyze_medical_content(self, text):
        """Analyze medical content and terms in the text"""
        text_lower = text.lower()
        analysis = {
            'disease_mentions': 0,
            'treatment_mentions': 0,
            'professional_mentions': 0,
            'facility_mentions': 0,
            'misinformation_indicators': 0,
            'scientific_terms': 0,
            'total_medical_terms': 0,
            'medical_categories': []
        }
        
        for category, terms in self.medical_terms.items():
            count = sum(1 for term in terms if term in text_lower)
            analysis[f'{category}_mentions'] = count
            analysis['total_medical_terms'] += count
            if count > 0:
                analysis['medical_categories'].append(category)
        
        return analysis

    def get_medical_recommendation(self, prediction, confidence, medical_analysis):
        """Provide medical-specific recommendations"""
        misinformation_score = medical_analysis.get('misinformation_indicators', 0)
        scientific_score = medical_analysis.get('scientific_terms', 0)
        
        if confidence < 0.6:
            return "Low confidence prediction. Always consult healthcare professionals for medical advice."
        elif prediction == 0:  # Fake/Misinformation
            if misinformation_score > 2:
                return "HIGH RISK: Multiple misinformation indicators detected. Consult licensed healthcare providers immediately."
            else:
                return "Potential misinformation detected. Verify with reputable medical sources and healthcare professionals."
        else:  # Real/Legitimate
            if scientific_score > 1:
                return "Contains scientific terminology. Still recommend consulting healthcare professionals for personal medical decisions."
            elif confidence > 0.8:
                return "Appears to be legitimate medical information. However, always consult healthcare professionals for medical advice."
            else:
                return "Possibly legitimate but verify with multiple reputable medical sources and professionals."

    def train_model(self):
        """Train the enhanced medical misinformation detection model"""
        print("\n" + "="*60)
        print("TRAINING COMPREHENSIVE MEDICAL MISINFORMATION DETECTOR")
        print("="*60)
        
        start_time = datetime.now()
        
        # Load and process datasets
        df = self.load_and_process_datasets()
        
        if len(df) == 0:
            raise Exception("No training data available")
        
        self.training_info = {
            'total_samples': len(df),
            'misinformation_samples': len(df[df['label'] == 0]),
            'legitimate_samples': len(df[df['label'] == 1]),
            'training_time': None,
            'accuracy': None,
            'sources': df['source_file'].unique().tolist()
        }
        
        print(f"\nPreprocessing {len(df)} medical text samples...")
        
        # Process texts in batches
        batch_size = 1000
        processed_texts = []
        
        for i in range(0, len(df), batch_size):
            batch_end = min(i + batch_size, len(df))
            batch_texts = df.iloc[i:batch_end]['text'].apply(self.preprocess_text)
            processed_texts.extend(batch_texts.tolist())
            print(f"Processed {batch_end}/{len(df)} texts...")
        
        df['processed_text'] = processed_texts
        df = df[df['processed_text'].str.len() > 5].reset_index(drop=True)
        
        print(f"Final training dataset: {len(df)} samples")
        
        # Prepare training data
        X = df['processed_text']
        y = df['label']
        
        # Split data with stratification
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Create TF-IDF vectors
        print("Creating TF-IDF feature vectors...")
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        print(f"Feature vector shape: {X_train_vec.shape}")
        
        # Train ensemble model
        print("Training enhanced ensemble model...")
        self.model.fit(X_train_vec, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation for robust evaluation
        cv_scores = cross_val_score(self.model, X_train_vec, y_train, cv=5, scoring='accuracy')
        
        # Generate detailed classification report
        class_report = classification_report(y_test, y_pred, target_names=['Misinformation', 'Legitimate'])
        
        end_time = datetime.now()
        training_duration = (end_time - start_time).total_seconds()
        
        # Update training info
        self.training_info.update({
            'accuracy': float(accuracy),
            'cv_mean_accuracy': float(cv_scores.mean()),
            'cv_std_accuracy': float(cv_scores.std()),
            'training_time': training_duration,
            'feature_count': X_train_vec.shape[1],
            'classification_report': class_report
        })
        
        self.is_trained = True
        
        print(f"\n" + "="*60)
        print("TRAINING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"Training Duration: {training_duration:.2f} seconds")
        print(f"Test Accuracy: {accuracy:.4f}")
        print(f"Cross-validation Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        print(f"Feature Count: {X_train_vec.shape[1]:,}")
        print(f"Training Sources: {', '.join(self.training_info['sources'])}")
        print("\nDetailed Classification Report:")
        print(class_report)
        
        # Save the trained model
        self.save_model()
        
        return accuracy

    def predict(self, text):
        """Enhanced prediction with medical analysis - FIXED TO RETURN fake/real"""
        if not self.is_trained:
            return {"error": "Model not trained", "success": False}

        # Input validation
        if not text or not isinstance(text, str):
            return {
                "success": False,
                "prediction": "uncertain",
                "confidence": 0.5,
                "message": "Invalid input text"
            }

        # Check text length
        if len(text.strip()) < 10:
            return {
                "success": False,
                "prediction": "uncertain",
                "confidence": 0.5,
                "message": "Text too short for reliable analysis (minimum 10 characters)"
            }

        if len(text) > 100000:
            return {
                "success": False,
                "prediction": "uncertain",
                "confidence": 0.5,
                "message": "Text too long (maximum 100,000 characters)"
            }

        try:
            # Preprocess text
            cleaned_text = self.preprocess_text(text)

            if len(cleaned_text.strip()) < 3:
                return {
                    "success": False,
                    "prediction": "uncertain",
                    "confidence": 0.5,
                    "message": "Text contains insufficient meaningful content for analysis"
                }

            # Vectorize and predict
            text_vec = self.vectorizer.transform([cleaned_text])
            prediction = self.model.predict(text_vec)[0]
            probabilities = self.model.predict_proba(text_vec)[0]
            confidence = float(max(probabilities))

            # Analyze medical content
            medical_analysis = self.analyze_medical_content(text.lower())

            # Calculate medical relevance score
            medical_relevance = "high" if medical_analysis['total_medical_terms'] > 3 else \
                              "medium" if medical_analysis['total_medical_terms'] > 1 else "low"

            # FIXED: Return fake/real instead of misinformation/legitimate
            result = {
                "success": True,
                "prediction": "real" if prediction == 1 else "fake",  # Changed this line
                "prediction_label": "Real/Factual Medical Information" if prediction == 1 else "Fake/Medical Misinformation",
                "confidence": confidence,
                "probability_fake": float(probabilities[0]),  # Changed from probability_misinformation
                "probability_real": float(probabilities[1]),  # Changed from probability_legitimate
                "medical_analysis": medical_analysis,
                "medical_relevance": medical_relevance,
                "recommendation": self.get_medical_recommendation(prediction, confidence, medical_analysis),
                "warning": "This is an AI prediction. Always consult qualified healthcare professionals for medical advice." if medical_analysis['total_medical_terms'] > 0 else None
            }

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Prediction error: {str(e)}",
                "prediction": "uncertain",
                "confidence": 0.5
            }

    def save_model(self):
        """Save the trained model and associated data"""
        os.makedirs('models', exist_ok=True)
        
        try:
            with open('models/medical_vectorizer.pkl', 'wb') as f:
                pickle.dump(self.vectorizer, f)
            with open('models/medical_model.pkl', 'wb') as f:
                pickle.dump(self.model, f)
            with open('models/medical_training_info.pkl', 'wb') as f:
                pickle.dump(self.training_info, f)
            with open('models/medical_terms.pkl', 'wb') as f:
                pickle.dump(self.medical_terms, f)
                
            print("Enhanced medical misinformation detection model saved successfully!")
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False

    def load_model(self):
        """Load pre-trained model and associated data"""
        try:
            with open('models/medical_vectorizer.pkl', 'rb') as f:
                self.vectorizer = pickle.load(f)
            with open('models/medical_model.pkl', 'rb') as f:
                self.model = pickle.load(f)
            with open('models/medical_training_info.pkl', 'rb') as f:
                self.training_info = pickle.load(f)
            with open('models/medical_terms.pkl', 'rb') as f:
                self.medical_terms = pickle.load(f)
            
            self.is_trained = True
            print("Pre-trained medical misinformation detection model loaded successfully!")
            return True
        except FileNotFoundError:
            print("No saved medical model found. Training new model...")
            return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def download_datasets(self):
        """Download popular medical misinformation datasets"""
        print("Dataset download feature - placeholder for future implementation")
        print("Recommended datasets to manually download:")
        print("1. FakeHealth Dataset: https://github.com/EnyanDai/FakeHealth")
        print("2. CoAID Dataset: https://github.com/cuilimeng/CoAID")
        print("3. HealthLies Dataset: Search for 'HealthLies healthcare misinformation dataset'")
        print("4. PUBHEALTH Dataset: https://github.com/neemakot/Health-Fact-Checking")
        return {"message": "Please download datasets manually and place in 'datasets' folder"}

# Initialize enhanced detector
detector = MedicalMisinformationDetector()

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check with model and dataset information"""
    return jsonify({
        "status": "healthy", 
        "service": "Enhanced Medical Misinformation Detection",
        "model_trained": detector.is_trained,
        "training_info": detector.training_info if detector.is_trained else None,
        "medical_categories": list(detector.medical_terms.keys()),
        "version": "2.0 - Comprehensive Medical Coverage"
    })

@app.route('/predict', methods=['POST'])
def predict_medical_claim():
    """Enhanced prediction endpoint for medical claims"""
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({"success": False, "error": "No text provided in request body"}), 400

        text = data['text'].strip()

        if len(text) < 10:
            return jsonify({
                "success": False, 
                "error": "Text too short for analysis (minimum 10 characters)",
                "recommendation": "Please provide more detailed text for accurate analysis"
            }), 400

        if len(text) > 100000:
            return jsonify({
                "success": False, 
                "error": "Text too long (maximum 100,000 characters)",
                "recommendation": "Please provide shorter text for analysis"
            }), 400

        # Get prediction
        result = detector.predict(text)
        
        if not result.get("success", True):
            return jsonify(result), 400

        # Add additional metadata
        result["service"] = "Enhanced Medical Misinformation Detection"
        result["timestamp"] = datetime.now().isoformat()
        
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False, 
            "error": f"Server error: {str(e)}",
            "service": "Enhanced Medical Misinformation Detection"
        }), 500

@app.route('/train', methods=['POST'])
def train_medical_model():
    """Train the enhanced medical misinformation detection model"""
    try:
        print("Starting enhanced medical misinformation model training...")
        accuracy = detector.train_model()
        return jsonify({
            "success": True, 
            "message": "Enhanced medical misinformation detection model trained successfully",
            "accuracy": accuracy,
            "training_info": detector.training_info,
            "service": "Enhanced Medical Misinformation Detection"
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": f"Training failed: {str(e)}",
            "service": "Enhanced Medical Misinformation Detection"
        }), 500

@app.route('/datasets', methods=['GET'])
def list_medical_datasets():
    """Get information about available medical datasets"""
    try:
        datasets_info = detector.discover_datasets()
        medical_datasets = [d for d in datasets_info if d['medical_score'] > 0]
        
        return jsonify({
            "success": True,
            "total_files": len(datasets_info),
            "medical_relevant_files": len(medical_datasets),
            "usable_files": len([d for d in datasets_info if d['usable']]),
            "datasets": datasets_info,
            "recommended_datasets": detector.dataset_sources,
            "service": "Enhanced Medical Misinformation Detection"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/download-datasets', methods=['POST'])
def download_datasets():
    """Download recommended medical misinformation datasets"""
    try:
        result = detector.download_datasets()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/model-info', methods=['GET'])
def enhanced_model_info():
    """Get detailed information about the enhanced model"""
    return jsonify({
        "service": "Enhanced Medical Misinformation Detection",
        "version": "2.0",
        "model_trained": detector.is_trained,
        "training_info": detector.training_info,
        "model_features": {
            "vectorizer": "TF-IDF with 1-4 grams for medical phrases",
            "classifier": "Enhanced Ensemble (Balanced LR + RF)",
            "max_features": 20000,
            "preprocessing": "Medical-aware text cleaning with term preservation",
            "medical_categories": len(detector.medical_terms),
            "total_medical_terms": sum(len(terms) for terms in detector.medical_terms.values())
        },
        "medical_categories": {
            category: len(terms) for category, terms in detector.medical_terms.items()
        },
        "capabilities": [
            "COVID-19 misinformation detection",
            "General medical misinformation detection",
            "Cancer treatment misinformation",
            "Vaccine misinformation",
            "Mental health misinformation",
            "Diet and nutrition misinformation",
            "Medical procedure misinformation"
        ]
    })

@app.route('/test-examples', methods=['GET'])
def get_test_examples():
    """Get example texts for testing the model"""
    examples = {
        "fake_examples": [  # Changed from misinformation_examples
            "Drinking bleach cures COVID-19 completely in 24 hours",
            "Cancer can be cured by drinking lemon water and positive thinking",
            "Vaccines cause autism and contain microchips for tracking",
            "Diabetes can be cured permanently by eating cinnamon daily",
            "Jaundice can be cured by drinking only sugarcane juice for weeks"
        ],
        "real_examples": [  # Changed from legitimate_examples
            "COVID-19 vaccines have been shown to reduce severe illness in clinical trials",
            "Cancer treatment typically involves surgery, chemotherapy, or radiation therapy",
            "Vaccines undergo rigorous safety testing before approval",
            "Diabetes management includes medication, diet, and regular monitoring",
            "Jaundice requires medical evaluation to determine underlying causes"
        ]
    }
    
    return jsonify({
        "success": True,
        "examples": examples,
        "note": "Use these examples to test the enhanced medical misinformation detection model"
    })

if __name__ == '__main__':
    print("\n" + "="*70)
    print("ENHANCED MEDICAL MISINFORMATION DETECTION SERVICE")
    print("="*70)
    print("🏥 Comprehensive Healthcare Misinformation Detection")
    print("🔍 Covers COVID-19, Cancer, Vaccines, Mental Health & More")
    print("🤖 Advanced ML with Medical-Aware Processing")
    print("="*70)
    print("\nAvailable endpoints:")
    print("• GET  /health           - Service health and model status")
    print("• POST /predict          - Predict if medical claim is fake or real")
    print("• POST /train            - Train model with available datasets")
    print("• GET  /datasets         - List and analyze available datasets")
    print("• POST /download-datasets - Get info on downloading datasets")
    print("• GET  /model-info       - Detailed model information")
    print("• GET  /test-examples    - Get example texts for testing")
    print("="*70)
    
    # Try to load existing model
    if not detector.load_model():
        print("\n🚀 No pre-trained model found. Training new model...")
        try:
            detector.train_model()
            print("✅ Model training completed successfully!")
        except Exception as e:
            print(f"⚠️  Training failed: {e}")
            print("📝 Service will start but model training will be required")
            print("💡 Try adding medical datasets to the 'datasets' folder")
    else:
        print("✅ Pre-trained model loaded successfully!")
    
    print(f"\n🌐 Starting Flask server on http://localhost:5000")
    print("📚 Add medical misinformation datasets to 'datasets' folder for better accuracy")
    print("🔬 Ready to detect medical misinformation!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
