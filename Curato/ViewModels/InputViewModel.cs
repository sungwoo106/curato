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

        public string CompanionButtonText => string.IsNullOrEmpty(SelectedCompanion) ? "Companion" : SelectedCompanion;

        public bool CompanionSelected => !string.IsNullOrEmpty(SelectedCompanion);

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
