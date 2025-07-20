using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
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

        public string LocationQuery { get; set; } = "Search Location";

        public ICommand GeneratePlanCommand { get; }

        public InputViewModel()
        {
            PopularPlaces = new ObservableCollection<PopularPlace>
            {
                new PopularPlace
                {
                    ImagePath = "/Resources/Images/seongsu.jpg",
                    Title = "Seongsu",
                    Subtitle = "New trendy area with cafes and restaurants",
                    Type = "Most Loved"
                },
                new PopularPlace
                {
                    ImagePath = "/Resources/Images/hongdae.jpg",
                    Title = "Hongdae ・ Mapo",
                    Subtitle = "Trendy, youthful culture and cafes",
                    Type = "Most Popular"
                },
                new PopularPlace
                {
                    ImagePath = "/Resources/Images/gangnam.jpg",
                    Title = "Gangnam ・ Yeoksam",
                    Subtitle = "Upscale shopping and nightlife",
                    Type = "Most Fancy"
                },
                new PopularPlace
                {
                    ImagePath = "/Resources/Images/itaewon.jpg",
                    Title = "Itaewon ・ Yongsan",
                    Subtitle = "Global vibes and cuisine",
                    Type = "Most Diverse"
                },
                new PopularPlace
                {
                    ImagePath = "/Resources/Images/bukchon.jpg",
                    Title = "Bukchon ・ Jongno",
                    Subtitle = "Traditional hanok village beauty",
                    Type = "Most Cultural"
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

        public event PropertyChangedEventHandler? PropertyChanged;
        protected void OnPropertyChanged([CallerMemberName] string? name = null) =>
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}
