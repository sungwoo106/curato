using System.Collections.ObjectModel;
using System.Collections.Generic;
using System.ComponentModel;
using System;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Windows.Input;
using Curato.Models;
using Curato.Helpers;

// <summary>
// InputViewModel manages the input data and commands for the application.
// </summary>

namespace Curato.ViewModels
{
    public class InputViewModel : INotifyPropertyChanged
    {
        public ObservableCollection<PopularPlace> PopularPlaces { get; set; }

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

        // The six category options
        public ObservableCollection<string> CategoryOptions { get; }
            = new ObservableCollection<string>
            { "Cafe", "Museum", "Park", "Shopping", "Restaurant", "Gallery" };

        // Track the single-selected category
        private string? _selectedCategory;
        public string? SelectedCategory
        {
            get => _selectedCategory;
            set
            {
                if (_selectedCategory != value)
                {
                    _selectedCategory = value;
                    OnPropertyChanged();
                    OnPropertyChanged(nameof(CategoryButtonText));
                    OnPropertyChanged(nameof(CategorySelected));
                }
            }
        }

        // Button text + accent flag
        public string CategoryButtonText
            => string.IsNullOrEmpty(SelectedCategory) ? "Category" : SelectedCategory;

        public bool CategorySelected
            => !string.IsNullOrEmpty(SelectedCategory);


        public string LocationQuery { get; set; } = "Search Location";

        public ICommand GeneratePlanCommand { get; }

        public InputViewModel()
        {
            foreach (var ct in FetchCompanionTypes())
                CompanionTypes.Add(ct);

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

            GeneratePlanCommand = new RelayCommand(_ => GeneratePlan());
        }

        private void GeneratePlan()
        {
            // Future: Connect your existing AI + API logic here
            // For now: simple placeholder action
            System.Diagnostics.Debug.WriteLine("Generate Plan Clicked");
        }

        private IEnumerable<string> FetchCompanionTypes()
        {
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = "python3",
                    Arguments = "-c \"import json, constants; print(json.dumps(constants.COMPANION_TYPES))\"",
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = Process.Start(psi)!;
                string output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();
                return JsonSerializer.Deserialize<List<string>>(output) ?? new List<string>();
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Failed to load companion types: {ex}");
                return new List<string> { "tSolo", "tCouple", "tFriends", "tFamily" };
            }
        }

        public event PropertyChangedEventHandler? PropertyChanged;
        protected void OnPropertyChanged([CallerMemberName] string? name = null) =>
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}
