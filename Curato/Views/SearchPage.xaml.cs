using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using Curato.ViewModels;

namespace Curato.Views
{
    public partial class SearchPage : UserControl
    {
        public SearchPage()
        {
            InitializeComponent();
            this.DataContext = new InputViewModel();
        }

        private void CompanionButton_Click(object sender, RoutedEventArgs e)
        {
            if (DataContext is not InputViewModel vm)
                return;

            var menu = new ContextMenu();
            foreach (string type in vm.CompanionTypes)
            {
                var item = new MenuItem { Header = type };
                item.Click += (s, _) => { vm.SelectedCompanion = type; };
                menu.Items.Add(item);
            }

            menu.PlacementTarget = sender as UIElement;
            menu.IsOpen = true;
        }
    }
}