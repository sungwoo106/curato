using System.Windows.Media;
using System.Windows.Controls.Primitives;
using System.Windows.Shapes;
using System.Windows.Media.Animation;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
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

            CompanionItemsControl.Items.Clear();

            foreach (string type in vm.CompanionTypes)
            {
                var isSelected = type == vm.SelectedCompanion;

                var dot = new Ellipse
                {
                    Width = 25,
                    Height = 25,
                    Fill = isSelected ? new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB31A")) : Brushes.LightGray,
                    VerticalAlignment = VerticalAlignment.Center,
                    Margin = new Thickness(0, 0, 10, 0)
                };

                var text = new TextBlock
                {
                    Text = type,
                    FontSize = 24,
                    Foreground = Brushes.Black,
                    VerticalAlignment = VerticalAlignment.Center,
                    FontFamily = new FontFamily("{StaticResource SatoshiMedium}")
                };

                var panel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    Children = { dot, text },
                    Margin = new Thickness(0, 5, 0, 0)
                };

                var container = new Border
                {
                    CornerRadius = new CornerRadius(8),
                    Background = Brushes.Transparent,
                    Child = panel,
                    Cursor = Cursors.Hand,
                    Padding = new Thickness(10, 10, 10, 10)
                };

                container.MouseLeftButtonUp += (_, _) =>
                {
                    vm.SelectedCompanion = type;
                    CompanionPopup.IsOpen = false;
                };

                CompanionItemsControl.Items.Add(container);
            }

            CompanionPopup.IsOpen = true;
        }

        private void BudgetButton_Click(object sender, RoutedEventArgs e)
        {
            if (DataContext is not InputViewModel vm)
                return;

            BudgetItemsControl.Items.Clear();

            foreach (var option in vm.BudgetOptions)
            {
                bool isSelected = option == vm.SelectedBudget;

                // yellow dot same as Companion
                var dot = new Ellipse
                {
                    Width = 25,
                    Height = 25,
                    Fill    = isSelected
                            ? (Brush)new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB31A"))
                            : Brushes.LightGray,
                    VerticalAlignment = VerticalAlignment.Center,
                    Margin = new Thickness(0, 0, 10, 0)
                };

                var text = new TextBlock
                {
                    Text = option,
                    FontSize = 24,
                    Foreground = Brushes.Black,
                    VerticalAlignment = VerticalAlignment.Center,
                    FontFamily = new FontFamily("{StaticResource SatoshiMedium}")
                };

                var panel = new StackPanel
                {
                    Orientation = Orientation.Horizontal,
                    Children = { dot, text },
                    Margin = new Thickness(0, 5, 0, 0)
                };

                var container = new Border
                {
                    CornerRadius = new CornerRadius(8),
                    Background = Brushes.Transparent,
                    Child = panel,
                    Cursor = Cursors.Hand,
                    Padding = new Thickness(10, 10, 10, 10)
                };

                container.MouseLeftButtonUp += (_, _) =>
                {
                    vm.SelectedBudget = option;
                    BudgetPopup.IsOpen = false;
                };

                BudgetItemsControl.Items.Add(container);
            }

            BudgetPopup.IsOpen = true;
        }

    }
}