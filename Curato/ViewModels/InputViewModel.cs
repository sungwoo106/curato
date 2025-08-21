using System.Collections.ObjectModel;
using System.Collections.Generic;
using System.ComponentModel;
using System;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Linq;
using System.IO;
using System.Text;
using Curato.Models;
using Curato.Helpers;

namespace Curato.ViewModels
{
    /// <summary>
    /// InputViewModel manages the input data and commands for the application.
    /// </summary>
    public class InputViewModel : INotifyPropertyChanged
    {
        public ObservableCollection<PopularPlace> PopularPlaces { get; set; } = new ObservableCollection<PopularPlace>();

        private ObservableCollection<PlaceSuggestion> _locationSuggestions = new();
        public ObservableCollection<PlaceSuggestion> LocationSuggestions
        {
            get => _locationSuggestions;
            set
            {
                _locationSuggestions = value;
                OnPropertyChanged(nameof(LocationSuggestions));
            }
        }

        private (double Latitude, double Longitude)? _selectedLocationCoordinates;
        public (double Latitude, double Longitude)? SelectedLocationCoordinates
        {
            get => _selectedLocationCoordinates;
            set
            {
                _selectedLocationCoordinates = value;
                OnPropertyChanged(nameof(SelectedLocationCoordinates));
            }
        }

        // The list of companion types
        public ObservableCollection<string> CompanionTypes { get; } = new ObservableCollection<string>();

        private string? _selectedCompanion;
        public string? SelectedCompanion
        {
            get => _selectedCompanion;
            set
            {
                if (_selectedCompanion != value)
                {
                    _selectedCompanion = value;
                    OnPropertyChanged();
                    OnPropertyChanged(nameof(CompanionButtonText));
                    OnPropertyChanged(nameof(CompanionSelected));
                    OnPropertyChanged(nameof(PreferencesSummary));
                }
            }
        }

        // What shows on the button
        public string CompanionButtonText => string.IsNullOrEmpty(SelectedCompanion) ? "Companion" : SelectedCompanion;

        // Helper for style trigger
        public bool CompanionSelected => !string.IsNullOrEmpty(SelectedCompanion);

        // The list of budget options
        public ObservableCollection<string> BudgetOptions { get; } 
            = new ObservableCollection<string> { "$", "$$", "$$$" };

        private string? _selectedBudget;
        public string? SelectedBudget
        {
            get => _selectedBudget;
            set
            {
                if (_selectedBudget != value)
                {
                    _selectedBudget = value;
                    OnPropertyChanged();                       // SelectedBudget
                    OnPropertyChanged(nameof(BudgetButtonText));
                    OnPropertyChanged(nameof(BudgetSelected));
                    OnPropertyChanged(nameof(PreferencesSummary));
                }
            }
        }

        // What shows on the button
        public string BudgetButtonText => string.IsNullOrEmpty(SelectedBudget) ? "Budget" : SelectedBudget;

        // Helper for style trigger
        public bool BudgetSelected => !string.IsNullOrEmpty(SelectedBudget);



        // The list of time options
        // Main options: Midnight, Morning, Afternoon, Evening
        // Sub-options: 00:00, 01:00, ..., 23:00
        public Dictionary<string, List<string>> TimeOptionsMap { get; }
            = new Dictionary<string, List<string>>
            {
                ["Midnight"] = new List<string> { "00:00", "01:00", "02:00", "03:00", "04:00", "05:00" },
                ["Morning"] = new List<string> { "06:00", "07:00", "08:00", "09:00", "10:00", "11:00" },
                ["Afternoon"] = new List<string> { "12:00", "13:00", "14:00", "15:00", "16:00", "17:00" },
                ["Evening"] = new List<string> { "18:00", "19:00", "20:00", "21:00", "22:00", "23:00" }
            };

        // For binding first row
        public IEnumerable<string> TimeMainOptions 
            => TimeOptionsMap.Keys;

        // Selected period & slot
        private string? _selectedMainTime;
        public string? SelectedMainTime
        {
            get => _selectedMainTime;
            set
            {
                if (_selectedMainTime != value)
                {
                    _selectedMainTime = value;
                    // reset sub-selection when main changes
                    SelectedSubTime = null;
                    OnPropertyChanged();
                    OnPropertyChanged(nameof(TimeButtonText));
                    OnPropertyChanged(nameof(TimeSelected));
                    OnPropertyChanged(nameof(PreferencesSummary));
                }
            }
        }

        private string? _selectedSubTime;
        public string? SelectedSubTime
        {
            get => _selectedSubTime;
            set
            {
                if (_selectedSubTime != value)
                {
                    _selectedSubTime = value;
                    OnPropertyChanged();
                    OnPropertyChanged(nameof(TimeButtonText));
                    OnPropertyChanged(nameof(TimeSelected));
                    OnPropertyChanged(nameof(PreferencesSummary));
                }
            }
        }

        // What shows on the button
        public string TimeButtonText
            => string.IsNullOrEmpty(SelectedSubTime)
                 ? "Time"
                 : SelectedSubTime;

        // Accent only once a sub-slot is chosen
        public bool TimeSelected
            => !string.IsNullOrEmpty(SelectedSubTime);

        // The list of place categories
        public ObservableCollection<string> CategoryOptions { get; } = new ObservableCollection<string>();

        // Categories the user has selected from the popup
        public ObservableCollection<string> SelectedCategories { get; } = new ObservableCollection<string>();

        public string SelectedCategoriesText => string.Join(", ", SelectedCategories);

        // Selected category for the button
        public string CategoryButtonText =>
            SelectedCategories.Count == 0 ?
            "Category" :
            string.Join(", ", SelectedCategories);

        // Helper for style trigger
        public bool CategorySelected => SelectedCategories.Count > 0;

        private string _locationQuery = "Search Location";
        public string LocationQuery
        {
            get => _locationQuery;
            set
            {
                if (_locationQuery != value)
                {
                    _locationQuery = value;
                    OnPropertyChanged();
                    OnPropertyChanged(nameof(PreferencesSummary));
                }
            }
        }

        private bool _isLocationPopupOpen;
        public bool IsLocationPopupOpen
        {
            get => _isLocationPopupOpen;
            set
            {
                if (_isLocationPopupOpen != value)
                {
                    _isLocationPopupOpen = value;
                    OnPropertyChanged(nameof(IsLocationPopupOpen));
                }
            }
        }

        public string PreferencesSummary => string.Join("    |    ", new[]
        {
            string.IsNullOrWhiteSpace(LocationQuery) || LocationQuery == "Search Location" ? null : LocationQuery,
            SelectedCompanion,
            SelectedBudget,
            string.IsNullOrWhiteSpace(SelectedSubTime) ? null : $"Start at {SelectedSubTime}",
            SelectedCategoriesText
        }.Where(s => !string.IsNullOrWhiteSpace(s)));





        public InputViewModel()
        {
            SelectedCategories.CollectionChanged += (_, __) =>
            {
                OnPropertyChanged(nameof(CategoryButtonText));
                OnPropertyChanged(nameof(CategorySelected));
                OnPropertyChanged(nameof(SelectedCategoriesText));
                OnPropertyChanged(nameof(PreferencesSummary));
            };
            foreach (var ct in FetchCompanionTypes())
                CompanionTypes.Add(ct);

            foreach (var cat in FetchCategories())
                CategoryOptions.Add(cat);

            PopularPlaces = new ObservableCollection<PopularPlace>
            {
                new PopularPlace
                {
                    ImagePath = "/Resources/Images/seongsu.jpg",
                    Title = "Seongsu",
                    Subtitle = "New trendy area with cafes and restaurants",
                    Label = "Most Loved"
                },
                new PopularPlace
                {
                    ImagePath = "/Resources/Images/hongdae.jpg",
                    Title = "Hongdae ・ Mapo",
                    Subtitle = "Trendy, youthful culture and cafes",
                    Label = "Most Popular"
                },
                new PopularPlace
                {
                    ImagePath = "/Resources/Images/gangnam.jpg",
                    Title = "Gangnam ・ Yeoksam",
                    Subtitle = "Upscale shopping and nightlife",
                    Label = "Most Fancy"
                },
                new PopularPlace
                {
                    ImagePath = "/Resources/Images/itaewon.jpg",
                    Title = "Itaewon ・ Yongsan",
                    Subtitle = "Global vibes and cuisine",
                    Label = "Most Diverse"
                },
                new PopularPlace
                {
                    ImagePath = "/Resources/Images/bukchon.jpg",
                    Title = "Bukchon ・ Jongno",
                    Subtitle = "Traditional hanok village beauty",
                    Label = "Most Cultural"
                }
            };


        }





        private IEnumerable<string> FetchCompanionTypes()
        {
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = "-c \"import json, constants; print(json.dumps(constants.COMPANION_TYPES, ensure_ascii=False))\"",
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                // Ensure proper UTF-8 encoding for Korean text
                psi.StandardOutputEncoding = Encoding.UTF8;

                using var process = Process.Start(psi)!;
                string output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();
                return JsonSerializer.Deserialize<List<string>>(output, new JsonSerializerOptions 
                { 
                    Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping 
                }) ?? new List<string>();
            }
            catch (Exception)
            {
                return new List<string> { "tSolo", "tCouple", "tFriends", "tFamily" };
            }
        }

        private IEnumerable<string> FetchCategories()
        {
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = "-c \"import json, constants; print(json.dumps(constants.USER_SELECTABLE_PLACE_TYPES, ensure_ascii=False))\"",
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                // Ensure proper UTF-8 encoding for Korean text
                psi.StandardOutputEncoding = Encoding.UTF8;

                using var process = Process.Start(psi)!;
                string output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();
                return JsonSerializer.Deserialize<List<string>>(output, new JsonSerializerOptions 
                { 
                    Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping 
                }) ?? new List<string>();
            }
            catch (Exception)
            {
                return new List<string> { "Cafe", "Restaurant", "Park" };
            }
        }

        public event PropertyChangedEventHandler? PropertyChanged;
        protected void OnPropertyChanged([CallerMemberName] string? name = null) =>
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}
