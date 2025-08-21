using System;
using System.Globalization;
using System.Windows.Data;

namespace Curato.Helpers
{
    /// <summary>
    /// Converts a count value to a boolean indicating if the count is positive
    /// </summary>
    public class PositiveCountToBoolConverter : IValueConverter
    {
        /// <summary>
        /// Converts a count to true if positive, false otherwise
        /// </summary>
        /// <param name="value">The count value to convert</param>
        /// <param name="targetType">The target type (bool)</param>
        /// <param name="parameter">Not used</param>
        /// <param name="culture">Not used</param>
        /// <returns>True if count > 0, false otherwise</returns>
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            return value is int count && count > 0;
        }

        /// <summary>
        /// ConvertBack is not implemented
        /// </summary>
        /// <exception cref="NotImplementedException">Always thrown as this converter is one-way</exception>
        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
